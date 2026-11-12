"""Supervision runtime: the mission machine and the simulated arm, ticked in time."""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable, Mapping
from enum import StrEnum
from types import MappingProxyType

from robot_core.adapters.sim.arm import SimArm
from robot_core.arm.kinematics import Kinematics, KinematicsUnavailableError
from robot_core.arm.model import load_preset
from robot_core.gateway.events import EventHub
from robot_core.gateway.telemetry import TelemetryData, build_snapshot
from robot_core.mission.machine import ChecklistItem, MissionMachine, Transition
from robot_core.mission.supervisor import Supervisor

logger = logging.getLogger(__name__)

SUPERVISION_PERIOD_S = 0.033  # REQ-MIS-008
TELEMETRY_PERIOD_S = 0.040  # REQ-GW-016
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
    `start` to `stop` (REQ-GW-020). Each phase change goes out on `events`, and so
    does a telemetry snapshot every 40 ms.

    Attributes:
        run_id: Identifier of this run of robot-core (REQ-REC-013).
        latest_telemetry: The latest snapshot pushed; None before `start`.

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
        self.run_id = str(uuid.uuid7())
        self.events = EventHub(self.run_id)
        self.arm = SimArm(time.monotonic, STOW_POSITION_RAD)
        self.machine = MissionMachine()
        self.supervisor = Supervisor(
            self.machine, self.arm, stow_position_rad=STOW_POSITION_RAD
        )
        self.latest_telemetry: TelemetryData | None = None
        self._kinematics_loaded = False
        self._last_tick_s: float | None = None
        self._latest_transition: Transition | None = None
        self._loops: list[asyncio.Task[None]] = []

    async def start(self) -> None:
        """End BOOT, then tick and push telemetry, once now and on in the background.

        The first tick and the first snapshot come before any request (REQ-GW-022).
        """
        try:
            self._kinematics_probe()
            self._kinematics_loaded = True
        except KinematicsUnavailableError as error:
            logger.warning("%s", error)
        self._announce(self.machine.complete_boot())
        self._tick()
        self._publish_telemetry()
        self._loops = [
            _start_loop("supervision loop", SUPERVISION_PERIOD_S, self._tick),
            _start_loop("telemetry", TELEMETRY_PERIOD_S, self._publish_telemetry),
        ]

    async def stop(self) -> None:
        """Stop the supervision loop and the telemetry."""
        for loop in self._loops:
            loop.cancel()
        await asyncio.gather(*self._loops, return_exceptions=True)

    def request_stop(self) -> None:
        """The operator's Stop: the arm stops at once, then SAFE_STOP (REQ-MIS-066)."""
        self._announce(self.supervisor.request_stop())

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

    def _tick(self) -> None:
        self._announce(self.supervisor.tick(self._checklist_evidence))
        self._last_tick_s = time.monotonic()

    def _publish_telemetry(self) -> None:
        assert self._latest_transition is not None, "BOOT ends before telemetry"
        self.latest_telemetry = build_snapshot(self.machine, self._latest_transition)
        self.events.publish_telemetry(self.latest_telemetry.model_dump(mode="json"))

    def _announce(self, transition: Transition | None) -> None:
        if transition is not None:
            self._latest_transition = transition
            self.events.publish_phase(transition)


def _start_loop(
    name: str, period_s: float, step: Callable[[], None]
) -> asyncio.Task[None]:
    loop = asyncio.create_task(_run_on_deadlines(name, period_s, step), name=name)
    loop.add_done_callback(_report_loop_end)
    return loop


async def _run_on_deadlines(
    name: str, period_s: float, step: Callable[[], None]
) -> None:
    """Run `step` on absolute deadlines; a late run is skipped, never run late."""
    deadline_s = time.monotonic()
    while True:
        deadline_s += period_s
        late_s = time.monotonic() - deadline_s
        if late_s > 0:
            if late_s > LATE_WARNING_PERIODS * period_s:
                logger.warning("%s %.0f ms late", name, late_s * 1000)
            deadline_s += (late_s // period_s + 1) * period_s
        await asyncio.sleep(deadline_s - time.monotonic())
        step()


def _report_loop_end(loop: asyncio.Task[None]) -> None:
    if not loop.cancelled() and (error := loop.exception()) is not None:
        logger.error("%s stopped", loop.get_name(), exc_info=error)
