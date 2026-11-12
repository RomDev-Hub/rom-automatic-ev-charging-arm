"""Simulated ArmPort: runs joint segments in memory against an injected clock.

The arm state is a pure function of the commands and the clock, so a run is
deterministic (REQ-SIM-031); stop holds the pose reached at once (REQ-SIM-001).
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Self

from robot_core.ports import PortCode, Refusal
from robot_core.ports.arm import (
    ArmHealth,
    ArmPort,
    ArmState,
    JointSegment,
    SegmentProgress,
    SegmentStatus,
)


@dataclass(frozen=True, slots=True)
class _Profile:
    """Time law of the leading joint: trapezoidal, or triangular when too short.

    A move too short to reach the velocity limit turns back half way.
    """

    distance_rad: float
    acceleration_rad_s2: float
    peak_velocity_rad_s: float
    ramp_s: float
    cruise_s: float

    @classmethod
    def plan(cls, distance_rad: float, segment: JointSegment) -> Self:
        acceleration = segment.max_acceleration_rad_s2
        if distance_rad == 0:
            return cls(0.0, acceleration, 0.0, 0.0, 0.0)
        peak = min(segment.max_velocity_rad_s, math.sqrt(distance_rad * acceleration))
        ramp_s = peak / acceleration
        cruise_s = max(0.0, distance_rad - peak * ramp_s) / peak
        return cls(distance_rad, acceleration, peak, ramp_s, cruise_s)

    @property
    def duration_s(self) -> float:
        return 2 * self.ramp_s + self.cruise_s

    def travelled_rad(self, elapsed_s: float) -> float:
        ramp_rad = 0.5 * self.acceleration_rad_s2 * self.ramp_s**2
        if elapsed_s <= self.ramp_s:
            return 0.5 * self.acceleration_rad_s2 * elapsed_s**2
        if elapsed_s <= self.ramp_s + self.cruise_s:
            return ramp_rad + self.peak_velocity_rad_s * (elapsed_s - self.ramp_s)
        remaining_s = self.duration_s - elapsed_s
        return self.distance_rad - 0.5 * self.acceleration_rad_s2 * remaining_s**2

    def velocity_rad_s(self, elapsed_s: float) -> float:
        if elapsed_s <= self.ramp_s:
            return self.acceleration_rad_s2 * elapsed_s
        if elapsed_s <= self.ramp_s + self.cruise_s:
            return self.peak_velocity_rad_s
        return self.acceleration_rad_s2 * (self.duration_s - elapsed_s)


@dataclass(frozen=True, slots=True)
class _Motion:
    """A segment in progress, with the pose and time it started from."""

    segment: JointSegment
    start_rad: tuple[float, ...]
    started_at_s: float
    profile: _Profile


class SimArm(ArmPort):
    """ArmPort adapter whose arm exists only in memory.

    The `simulate_*` methods fail the link the way a device can, so the rules
    for stale, missing or faulted arm data can be exercised (REQ-MOT-024). The
    simulated controller runs a segment to its end even while unreachable.
    """

    def __init__(
        self, clock: Callable[[], float], initial_position_rad: Sequence[float]
    ) -> None:
        self._clock = clock
        self._rest_rad = tuple(initial_position_rad)
        self._rest_progress: SegmentProgress | None = None
        self._motion: _Motion | None = None
        self._connected = True
        self._fault: PortCode | None = None
        self._stale_sample: ArmState | None = None

    def execute(self, segment: JointSegment) -> Refusal | None:
        if not self._connected:
            return Refusal(PortCode.DISCONNECTED)
        if self._fault is not None:
            return Refusal(self._fault)
        now_s = self._clock()
        start_rad = self._sample(now_s).joint_position_rad
        if len(segment.target_rad) != len(start_rad):
            return Refusal(PortCode.DIMENSION_MISMATCH)
        distance_rad = max(
            abs(target - start)
            for target, start in zip(segment.target_rad, start_rad, strict=True)
        )
        self._motion = _Motion(
            segment, start_rad, now_s, _Profile.plan(distance_rad, segment)
        )
        return None

    def stop(self) -> Refusal | None:
        if not self._connected:
            return Refusal(PortCode.DISCONNECTED)
        sample = self._sample(self._clock())
        progress = sample.progress
        if progress is not None and progress.status is SegmentStatus.RUNNING:
            progress = replace(progress, status=SegmentStatus.STOPPED)
        self._rest_rad = sample.joint_position_rad
        self._rest_progress = progress
        self._motion = None
        return None

    def read_state(self) -> ArmState | None:
        if not self._connected:
            return None
        if self._stale_sample is not None:
            return self._stale_sample
        return self._sample(self._clock())

    def read_health(self) -> ArmHealth:
        return ArmHealth(connected=self._connected, fault=self._fault)

    def simulate_stale_data(self) -> None:
        """Freeze the reported sample while the arm moves on."""
        if self._stale_sample is None:
            self._stale_sample = self._sample(self._clock())

    def simulate_disconnect(self) -> None:
        """Drop the link: no measurement, and every command is refused."""
        self._connected = False

    def simulate_adapter_fault(self) -> None:
        """Latch an adapter fault: new segments are refused, stop still works."""
        self._fault = PortCode.ADAPTER_FAULT

    def clear_simulated_failures(self) -> None:
        """Restore a connected, fault-free link with fresh samples."""
        self._connected = True
        self._fault = None
        self._stale_sample = None

    def _sample(self, now_s: float) -> ArmState:
        motion = self._motion
        if motion is None:
            return ArmState(
                joint_position_rad=self._rest_rad,
                joint_velocity_rad_s=(0.0,) * len(self._rest_rad),
                measured_at_s=now_s,
                progress=self._rest_progress,
            )
        elapsed_s = now_s - motion.started_at_s
        profile = motion.profile
        if elapsed_s >= profile.duration_s:
            return ArmState(
                joint_position_rad=motion.segment.target_rad,
                joint_velocity_rad_s=(0.0,) * len(motion.start_rad),
                measured_at_s=now_s,
                progress=SegmentProgress(
                    segment=motion.segment,
                    status=SegmentStatus.COMPLETED,
                    fraction=1.0,
                ),
            )
        share = profile.travelled_rad(elapsed_s) / profile.distance_rad
        rate = profile.velocity_rad_s(elapsed_s) / profile.distance_rad
        deltas = [
            target - start
            for target, start in zip(
                motion.segment.target_rad, motion.start_rad, strict=True
            )
        ]
        return ArmState(
            joint_position_rad=tuple(
                start + delta * share
                for start, delta in zip(motion.start_rad, deltas, strict=True)
            ),
            joint_velocity_rad_s=tuple(delta * rate for delta in deltas),
            measured_at_s=now_s,
            progress=SegmentProgress(
                segment=motion.segment, status=SegmentStatus.RUNNING, fraction=share
            ),
        )
