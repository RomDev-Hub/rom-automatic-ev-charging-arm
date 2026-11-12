"""Supervision runtime: the mission machine and the simulated arm, ticked in time."""

import asyncio
import logging
import time
from collections.abc import Callable, Mapping
from enum import StrEnum
from types import MappingProxyType

from robot_core.adapters.sim.arm import SimArm
from robot_core.arm.kinematics import Kinematics, KinematicsUnavailableError
from robot_core.arm.model import load_preset
from robot_core.mission.machine import ChecklistItem, MissionMachine
from robot_core.mission.supervisor import Supervisor

logger = logging.getLogger(__name__)

SUPERVISION_PERIOD_S = 0.033  # REQ-MIS-008
LATE_WARNING_PERIODS = 3  # REQ-MIS-008
TICK_MAX_AGE_S = 1.0  # REQ-GW-023
ARM_MODEL = "ur10e"
# Stow pose of the simulated arm until station configuration declares one.
STOW_POSITION_RAD = (0.0, -1.5708, 2.618, -1.0472, -1.5708, 0.0)
NO_EVIDENCE: Mapping[ChecklistItem, bool | None] = MappingProxyType({})


class HealthCheck(StrEnum):
    """Checks behind /api/health (REQ-GW-023)."""

    SUPERVISION_LOOP = "supervision_loop"
    ARM_PORT = "arm_port"
    KINEMATICS = "kinematics"


def probe_kinematics() -> None:
    """Load the kinematics of the arm model; raises KinematicsUnavailableError."""
    Kinematics(load_preset(ARM_MODEL))


class CoreRuntime:
    """Mission machine and simulated arm, ticked by the supervision loop.

    Building a runtime touches no device and starts no task; everything runs from
    `start` to `stop` (REQ-GW-020).

    Args:
        checklist_evidence: Checks whose sources the supervisor does not read, read
            again on every tick. No source has a port yet, so by default no check
            has data and the machine stays in SAFE_HOLD (REQ-MIS-015).
        kinematics_probe: Loads the kinematics library, raising
            KinematicsUnavailableError where it cannot.
    """

    def __init__(
        self,
        *,
        checklist_evidence: Mapping[ChecklistItem, bool | None] = NO_EVIDENCE,
        kinematics_probe: Callable[[], None] = probe_kinematics,
    ) -> None:
        self._checklist_evidence = checklist_evidence
        self._kinematics_probe = kinematics_probe
        self.arm = SimArm(time.monotonic, STOW_POSITION_RAD)
        self.machine = MissionMachine()
        self.supervisor = Supervisor(
            self.machine, self.arm, stow_position_rad=STOW_POSITION_RAD
        )
        self._kinematics_loaded = False
        self._last_tick_s: float | None = None
        self._loop: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """End BOOT, tick once, then keep ticking in the background (REQ-GW-022)."""
        try:
            self._kinematics_probe()
            self._kinematics_loaded = True
        except KinematicsUnavailableError as error:
            logger.warning("%s", error)
        self.machine.complete_boot()
        self._tick()
        self._loop = asyncio.create_task(
            self._supervise(time.monotonic()), name="supervision-loop"
        )
        self._loop.add_done_callback(_report_loop_end)

    async def stop(self) -> None:
        """Stop the supervision loop."""
        if self._loop is not None:
            self._loop.cancel()
            await asyncio.gather(self._loop, return_exceptions=True)

    def failing_health_checks(self) -> list[HealthCheck]:
        """Health checks failing now, in a fixed order (REQ-GW-023)."""
        last_tick_s = self._last_tick_s
        passed = {
            HealthCheck.SUPERVISION_LOOP: last_tick_s is not None
            and time.monotonic() - last_tick_s <= TICK_MAX_AGE_S,
            HealthCheck.ARM_PORT: self.supervisor.arm_data_fault() is None,
            HealthCheck.KINEMATICS: self._kinematics_loaded,
        }
        return [check for check, ok in passed.items() if not ok]

    async def _supervise(self, deadline_s: float) -> None:
        """Tick on absolute deadlines; a late tick is skipped, never run late."""
        while True:
            deadline_s += SUPERVISION_PERIOD_S
            late_s = time.monotonic() - deadline_s
            if late_s > 0:
                if late_s > LATE_WARNING_PERIODS * SUPERVISION_PERIOD_S:
                    logger.warning("supervision loop %.0f ms late", late_s * 1000)
                deadline_s += (
                    late_s // SUPERVISION_PERIOD_S + 1
                ) * SUPERVISION_PERIOD_S
            await asyncio.sleep(deadline_s - time.monotonic())
            self._tick()

    def _tick(self) -> None:
        self.supervisor.tick(self._checklist_evidence)
        self._last_tick_s = time.monotonic()


def _report_loop_end(loop: asyncio.Task[None]) -> None:
    if not loop.cancelled() and (error := loop.exception()) is not None:
        logger.error("supervision loop stopped", exc_info=error)
