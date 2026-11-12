"""Simulated ArmPort, on a virtual clock."""

from robot_core.adapters.sim.arm import SimArm
from robot_core.ports import Refusal
from robot_core.ports.arm import (
    ArmHealth,
    JointSegment,
    SegmentProgress,
    SegmentStatus,
)

START_RAD = (0.0, 0.0)
# Leading joint 1 rad at 0.5 rad/s and 1 rad/s²: 0.5 s ramps around 1.5 s of cruise.
SEGMENT = JointSegment(
    target_rad=(1.0, 0.5), max_velocity_rad_s=0.5, max_acceleration_rad_s2=1.0
)


def test_segment_runs_the_leading_joint_on_a_trapezoidal_profile(clock) -> None:
    """REQ-SIM-001: position, velocity and progress follow the limits in time."""
    arm = SimArm(clock, START_RAD)
    assert arm.execute(SEGMENT) is None

    clock.advance(0.5)
    state = arm.read_state()
    assert state.joint_position_rad == (0.125, 0.0625)
    assert state.joint_velocity_rad_s == (0.5, 0.25)
    assert state.progress == SegmentProgress(
        segment=SEGMENT, status=SegmentStatus.RUNNING, fraction=0.125
    )

    clock.advance(1.75)
    state = arm.read_state()
    assert state.joint_position_rad == (0.96875, 0.484375)
    assert state.joint_velocity_rad_s == (0.25, 0.125)

    clock.advance(0.25)
    state = arm.read_state()
    assert state.joint_position_rad == (1.0, 0.5)
    assert state.joint_velocity_rad_s == (0.0, 0.0)
    assert state.measured_at_s == 1002.5
    assert state.progress == SegmentProgress(
        segment=SEGMENT, status=SegmentStatus.COMPLETED, fraction=1.0
    )


def test_short_segment_turns_back_below_its_velocity_limit(clock) -> None:
    """REQ-SIM-001: a move too short to cruise peaks below the velocity limit."""
    arm = SimArm(clock, START_RAD)
    arm.execute(
        JointSegment(
            target_rad=(0.25, 0.0), max_velocity_rad_s=1.0, max_acceleration_rad_s2=1.0
        )
    )

    clock.advance(0.5)
    state = arm.read_state()
    assert state.joint_velocity_rad_s == (0.5, 0.0)
    assert state.progress.fraction == 0.5

    clock.advance(0.5)
    assert arm.read_state().progress.status is SegmentStatus.COMPLETED


def test_stop_holds_the_pose_reached(clock) -> None:
    """REQ-SIM-001: stop keeps the arm where it was when the stop arrived."""
    arm = SimArm(clock, START_RAD)
    arm.execute(SEGMENT)
    clock.advance(1.25)

    assert arm.stop() is None

    clock.advance(5.0)
    state = arm.read_state()
    assert state.joint_position_rad == (0.5, 0.25)
    assert state.joint_velocity_rad_s == (0.0, 0.0)
    assert state.progress == SegmentProgress(
        segment=SEGMENT, status=SegmentStatus.STOPPED, fraction=0.5
    )


def test_next_segment_starts_from_the_measured_pose(clock) -> None:
    """REQ-HAL-013: a new segment starts where the arm is, not at the old target."""
    arm = SimArm(clock, START_RAD)
    arm.execute(SEGMENT)
    clock.advance(1.25)

    arm.execute(
        JointSegment(
            target_rad=(0.0, 0.0), max_velocity_rad_s=0.5, max_acceleration_rad_s2=1.0
        )
    )

    clock.advance(0.5)
    assert arm.read_state().joint_position_rad == (0.375, 0.1875)


def test_stale_data_keeps_reporting_one_sample_while_the_arm_moves_on(clock) -> None:
    """REQ-MOT-024: stale data keeps its measurement time, so its age grows."""
    arm = SimArm(clock, START_RAD)
    arm.execute(SEGMENT)
    clock.advance(0.5)

    arm.simulate_stale_data()
    clock.advance(0.75)

    state = arm.read_state()
    assert state.measured_at_s == 1000.5
    assert state.joint_position_rad == (0.125, 0.0625)
    arm.clear_simulated_failures()
    assert arm.read_state().joint_position_rad == (0.5, 0.25)


def test_disconnected_arm_has_no_measurement_and_refuses_commands(clock) -> None:
    """REQ-HAL-004: without a link there is no measurement, not a zero."""
    arm = SimArm(clock, START_RAD)

    arm.simulate_disconnect()

    assert arm.read_state() is None
    assert arm.read_health() == ArmHealth(connected=False, fault=None)
    assert arm.execute(SEGMENT) == Refusal("port.disconnected")
    assert arm.stop() == Refusal("port.disconnected")


def test_adapter_fault_refuses_segments_but_not_stop(clock) -> None:
    """REQ-MOT-024: a latched adapter fault shows in health and blocks segments."""
    arm = SimArm(clock, START_RAD)

    arm.simulate_adapter_fault()

    assert arm.read_health() == ArmHealth(connected=True, fault="port.adapter_fault")
    assert arm.execute(SEGMENT) == Refusal("port.adapter_fault")
    assert arm.stop() is None


def test_segment_for_another_joint_count_is_refused(clock) -> None:
    """REQ-HAL-010: a segment whose joint count differs from the arm's is refused."""
    arm = SimArm(clock, START_RAD)

    refusal = arm.execute(
        JointSegment(
            target_rad=(1.0,), max_velocity_rad_s=0.5, max_acceleration_rad_s2=1.0
        )
    )

    assert refusal == Refusal("port.dimension_mismatch")
    assert arm.read_state().progress is None
