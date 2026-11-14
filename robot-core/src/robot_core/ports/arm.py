"""ArmPort: hands arm motion to the controller as whole segments (ADR 0004).

Units are SI and named in each field; times are on the host monotonic clock.
"""

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from robot_core.ports import PortCode, Refusal


@dataclass(frozen=True, slots=True, kw_only=True)
class JointSegment:
    """A joint-space move (moveJ) that the controller runs on its own to the end.

    All joints start and arrive together; the leading joint, the one with the
    largest displacement, keeps within the velocity and acceleration limits.
    """

    target_rad: tuple[float, ...]
    max_velocity_rad_s: float
    max_acceleration_rad_s2: float

    def __post_init__(self) -> None:
        if not self.target_rad:
            raise ValueError("a segment needs at least one joint target")
        limits = (self.max_velocity_rad_s, self.max_acceleration_rad_s2)
        if not all(math.isfinite(value) for value in (*self.target_rad, *limits)):
            raise ValueError("segment values must be finite")
        if min(limits) <= 0:
            raise ValueError("segment velocity and acceleration must be positive")


class SegmentStatus(StrEnum):
    """Where the controller stands with a segment."""

    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


@dataclass(frozen=True, slots=True, kw_only=True)
class SegmentProgress:
    """Progress of the latest segment.

    Attributes:
        fraction: Share of the leading joint's path covered, from 0 to 1.
    """

    segment: JointSegment
    status: SegmentStatus
    fraction: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ArmState:
    """One measured sample of the arm (REQ-HAL-009).

    Attributes:
        measured_at_s: Host monotonic time of the measurement.
        progress: Progress of the latest segment; None before the first one.
    """

    joint_position_rad: tuple[float, ...]
    joint_velocity_rad_s: tuple[float, ...]
    measured_at_s: float
    progress: SegmentProgress | None

    def age_s(self, now_s: float) -> float:
        """Seconds since the measurement, given a time on the same clock."""
        return now_s - self.measured_at_s


@dataclass(frozen=True, slots=True, kw_only=True)
class ArmHealth:
    """Link and fault state of the port (REQ-HAL-005).

    Attributes:
        fault: Code of the fault the adapter has latched; None when clear.
    """

    connected: bool
    fault: PortCode | None


class ArmPort(Protocol):
    """Port of the arm controller; one ArmPort is active at a time (REQ-HAL-009)."""

    def execute(self, segment: JointSegment) -> Refusal | None:
        """Hand a whole segment to the controller; None once it is passed on.

        A segment handed over while another runs replaces it, starting from the
        measured pose (REQ-HAL-013).
        """
        ...

    def stop(self) -> Refusal | None:
        """Stop the running segment and hold the arm still; None once passed on.

        An operational stop, never an emergency stop (REQ-HAL-021). With no
        segment running it changes nothing, so it may be repeated every tick.
        """
        ...

    def read_state(self) -> ArmState | None:
        """Latest measured sample; None when the port has no measurement."""
        ...

    def read_health(self) -> ArmHealth:
        """Link and latched-fault state of the port."""
        ...
