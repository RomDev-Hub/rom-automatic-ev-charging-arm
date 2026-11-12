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


type ParamValue = str | int | float | bool | None
type Params = Mapping[str, ParamValue]

EXPECTED_NEXT: Mapping[Phase, Phase] = MappingProxyType(
    {Phase.BOOT: Phase.SAFE_HOLD, Phase.SAFE_HOLD: Phase.S0_IDLE}
)


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

    def complete_boot(self) -> Transition | None:
        """End BOOT in SAFE_HOLD; no start enters S0_IDLE directly (REQ-MIS-013).

        Returns None when the machine has already left BOOT.
        """
        if self._phase is not Phase.BOOT:
            return None
        return self._enter(Phase.SAFE_HOLD, Reason.BOOT_READY)

    def _enter(self, phase: Phase, code: Reason) -> Transition:
        transition = Transition(
            previous=self._phase,
            phase=phase,
            code=code,
            params=MappingProxyType({}),
            expected_next=EXPECTED_NEXT.get(phase),
        )
        self._phase = phase
        self._entered_at_s = self._clock()
        return transition
