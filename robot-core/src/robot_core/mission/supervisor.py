"""Supervision tick: reads the arm port into the FSM snapshot, keeps a held arm still."""

import time
from collections.abc import Callable, Mapping, Sequence

from robot_core.mission.machine import (
    ChecklistItem,
    MissionMachine,
    Phase,
    Snapshot,
    Transition,
)
from robot_core.ports import PortCode
from robot_core.ports.arm import ArmPort, ArmState

# Fixed by the stow pose definition in docs/requirements/mission-motion-arm.md.
STOW_TOLERANCE_RAD = 0.12


class Supervisor:
    """Runs one supervision tick per call; the caller owns the loop and its period.

    Arm data that is stale (older than `max_arm_data_age_s`), missing or faulted
    forces SAFE_HOLD (REQ-MOT-024); while the machine holds, every tick asks the
    arm to stop (REQ-MIS-015, REQ-MOT-015).
    """

    def __init__(
        self,
        machine: MissionMachine,
        arm: ArmPort,
        *,
        stow_position_rad: Sequence[float],
        clock: Callable[[], float] = time.monotonic,
        max_arm_data_age_s: float = 0.15,
    ) -> None:
        self._machine = machine
        self._arm = arm
        self._stow_position_rad = tuple(stow_position_rad)
        self._clock = clock
        self._max_arm_data_age_s = max_arm_data_age_s

    def tick(self, evidence: Mapping[ChecklistItem, bool | None]) -> Transition | None:
        """Read the arm once, step the machine, then stop the arm while it holds.

        `evidence` carries the checks whose sources are not read here;
        `chk.motion_port` always comes from the arm port itself.
        """
        transition = self._machine.step(self._snapshot(evidence))
        if self._machine.phase is Phase.SAFE_HOLD:
            self._arm.stop()  # refused while the link is down, so sent every tick
        return transition

    def _snapshot(self, evidence: Mapping[ChecklistItem, bool | None]) -> Snapshot:
        arm = self._read_arm()
        if isinstance(arm, PortCode):
            return Snapshot(
                checklist={**evidence, ChecklistItem.MOTION_PORT: False},
                arm_stowed=None,
                arm_data_fault=arm,
            )
        return Snapshot(
            checklist={**evidence, ChecklistItem.MOTION_PORT: True},
            arm_stowed=self._is_stowed(arm),
            arm_data_fault=None,
        )

    def _read_arm(self) -> ArmState | PortCode:
        """The arm state when it can be trusted, else the code telling why not."""
        health = self._arm.read_health()
        if health.fault is not None:
            return health.fault
        state = self._arm.read_state()
        if not health.connected or state is None:
            return PortCode.DISCONNECTED
        if state.age_s(self._clock()) > self._max_arm_data_age_s:
            return PortCode.STALE_DATA
        return state

    def _is_stowed(self, state: ArmState) -> bool:
        return all(
            abs(joint - stow) < STOW_TOLERANCE_RAD
            for joint, stow in zip(
                state.joint_position_rad, self._stow_position_rad, strict=True
            )
        )
