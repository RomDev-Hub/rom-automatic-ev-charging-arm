"""ArmPort segment commands."""

import math

import pytest

from robot_core.ports.arm import JointSegment


@pytest.mark.parametrize(
    ("target_rad", "max_velocity_rad_s", "max_acceleration_rad_s2", "reason"),
    [
        ((0.0, math.nan), 1.0, 1.0, "finite"),
        ((0.0, 0.0), math.inf, 1.0, "finite"),
        ((0.0, 0.0), 1.0, -math.inf, "finite"),
        ((0.0, 0.0), 0.0, 1.0, "positive"),
        ((0.0, 0.0), 1.0, -1.0, "positive"),
        ((), 1.0, 1.0, "at least one joint"),
    ],
    ids=[
        "nan-target",
        "infinite-velocity",
        "infinite-acceleration",
        "zero-velocity",
        "negative-acceleration",
        "no-joint",
    ],
)
def test_segment_no_controller_could_run_cannot_be_built(
    target_rad, max_velocity_rad_s, max_acceleration_rad_s2, reason
) -> None:
    """REQ-HAL-010: a non-finite or meaningless segment never reaches an adapter."""
    with pytest.raises(ValueError, match=reason):
        JointSegment(
            target_rad=target_rad,
            max_velocity_rad_s=max_velocity_rad_s,
            max_acceleration_rad_s2=max_acceleration_rad_s2,
        )
