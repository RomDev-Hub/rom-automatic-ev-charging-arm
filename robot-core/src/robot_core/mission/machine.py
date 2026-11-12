"""Mission state machine: phases, reason codes and the single transition gate."""

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class Phase(StrEnum):
    """Phases of the mission state machine, named as in contracts/asyncapi.yaml."""

    BOOT = "BOOT"
    SAFE_HOLD = "SAFE_HOLD"
    S0_IDLE = "S0_IDLE"


class Reason(StrEnum):
    """Stable reason codes carried by transitions (REQ-MIS-003)."""

    BOOT_READY = "fsm.boot.ready"
    IDLE_AFTER_SAFE_HOLD = "fsm.idle.after_safe_hold"
    SAFE_HOLD_ARM_DATA = "fsm.safe_hold.arm_data"


class ChecklistItem(StrEnum):
    """Checks that must all pass before SAFE_HOLD ends (REQ-MIS-015)."""

    MOTION_PORT = "chk.motion_port"
    KINEMATICS = "chk.kinematics"
    COLLISION = "chk.collision"
    CAMERA = "chk.camera"
    CALIB = "chk.calib"
    ESTOP = "chk.estop"
    SAFETY_LEVEL = "chk.safety_level"


type ParamValue = str | int | float | bool | None
type Params = Mapping[str, ParamValue]

EXPECTED_NEXT: Mapping[Phase, Phase] = MappingProxyType(
    {Phase.BOOT: Phase.SAFE_HOLD, Phase.SAFE_HOLD: Phase.S0_IDLE}
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Snapshot:
    """Inputs of one step, read once per supervision tick (REQ-MIS-009).

    Attributes:
        checklist: Result of each check; None, or no entry, means no data.
        arm_stowed: Whether every measured joint is at the stow pose; None when
            not measured.
        arm_data_fault: Port code telling why the arm data cannot be trusted,
            such as `port.stale_data`; None when it can.
    """

    checklist: Mapping[ChecklistItem, bool | None]
    arm_stowed: bool | None
    arm_data_fault: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class Transition:
    """One phase change, with the fields of the phaseChanged event (REQ-MIS-002)."""

    previous: Phase
    phase: Phase
    code: Reason
    params: Params
    expected_next: Phase | None


class MissionMachine:
    """Mission state machine; every phase change passes through one gate.

    The machine reads no device and starts no thread: inputs arrive through its
    methods and time comes from the injected monotonic clock (REQ-MIS-006).
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._phase = Phase.BOOT
        self._entered_at_s = clock()
        self._failing_checks: tuple[ChecklistItem, ...] = tuple(ChecklistItem)

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def expected_next(self) -> Phase | None:
        """Phase entered once the current one's waiting condition is met (REQ-MIS-005).

        None when the catalogue holds no successor for the current phase.
        """
        return EXPECTED_NEXT.get(self._phase)

    @property
    def time_in_phase_s(self) -> float:
        """Seconds spent in the current phase, on the injected clock."""
        return self._clock() - self._entered_at_s

    @property
    def failing_checks(self) -> tuple[ChecklistItem, ...]:
        """Checks that failed the latest SAFE_HOLD evaluation; all until one runs.

        A check passes only on an explicit True: missing or unknown data fails.
        """
        return self._failing_checks

    def complete_boot(self) -> Transition | None:
        """End BOOT in SAFE_HOLD; no start enters S0_IDLE directly (REQ-MIS-013).

        Returns None when the machine has already left BOOT.
        """
        if self._phase is not Phase.BOOT:
            return None
        return self._enter(Phase.SAFE_HOLD, Reason.BOOT_READY)

    def step(self, snapshot: Snapshot) -> Transition | None:
        """Advance the machine on one snapshot.

        Untrusted arm data forces SAFE_HOLD from any phase (REQ-MOT-024). SAFE_HOLD
        ends in S0_IDLE only on evidence, never on elapsed time: every check passes
        and the arm is measured at its stow pose (REQ-MIS-017).
        """
        if self._phase is Phase.SAFE_HOLD:
            self._failing_checks = tuple(
                item
                for item in ChecklistItem
                if snapshot.checklist.get(item) is not True
            )
        if snapshot.arm_data_fault is not None:
            return self.force_safe_hold(
                Reason.SAFE_HOLD_ARM_DATA, {"cause": snapshot.arm_data_fault}
            )
        if (
            self._phase is Phase.SAFE_HOLD
            and not self._failing_checks
            and snapshot.arm_stowed is True
        ):
            return self._enter(Phase.S0_IDLE, Reason.IDLE_AFTER_SAFE_HOLD)
        return None

    def force_safe_hold(
        self, code: Reason, params: Params | None = None
    ) -> Transition | None:
        """Enter SAFE_HOLD from any phase with a `fsm.safe_hold.*` reason.

        Returns None when the machine is already holding.
        """
        return self._enter(Phase.SAFE_HOLD, code, params)

    def _enter(
        self, phase: Phase, code: Reason, params: Params | None = None
    ) -> Transition | None:
        """The single gate of every phase change (REQ-MIS-002)."""
        if phase is self._phase:
            return None
        transition = Transition(
            previous=self._phase,
            phase=phase,
            code=code,
            params=MappingProxyType(dict(params or {})),
            expected_next=EXPECTED_NEXT.get(phase),
        )
        self._phase = phase
        self._entered_at_s = self._clock()
        if phase is Phase.SAFE_HOLD:
            self._failing_checks = tuple(ChecklistItem)
        return transition
