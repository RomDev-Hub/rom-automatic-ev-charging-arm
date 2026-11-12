"""Supervision tick driving the simulated arm, on a virtual clock."""

from robot_core.adapters.sim.arm import SimArm
from robot_core.mission.machine import ChecklistItem, MissionMachine, Phase, Transition
from robot_core.mission.supervisor import Supervisor
from robot_core.ports.arm import JointSegment, SegmentProgress, SegmentStatus

TICK_S = 0.03125  # 32 Hz, exact in binary floating point
STOW_RAD = (0.0, -1.5708, 2.618, -1.0472, -1.5708, 0.0)
EVIDENCE = {
    item: True for item in ChecklistItem if item is not ChecklistItem.MOTION_PORT
}
# Leading joint 1 rad at 0.5 rad/s and 1 rad/s²: 0.5 s ramps around 1.5 s of cruise.
SEGMENT = JointSegment(
    target_rad=(1.0, *STOW_RAD[1:]), max_velocity_rad_s=0.5, max_acceleration_rad_s2=1.0
)


class Station:
    """Machine, simulated arm and supervisor on one virtual clock."""

    def __init__(self, clock) -> None:
        self.clock = clock
        self.arm = SimArm(clock, STOW_RAD)
        self.machine = MissionMachine(clock)
        self.supervisor = Supervisor(
            self.machine, self.arm, stow_position_rad=STOW_RAD, clock=clock
        )

    def tick(self, evidence=EVIDENCE) -> Transition | None:
        self.clock.advance(TICK_S)
        return self.supervisor.tick(evidence)


def idle_with_segment_half_done(clock) -> Station:
    station = Station(clock)
    station.machine.complete_boot()
    station.tick()
    assert station.machine.phase is Phase.S0_IDLE
    station.arm.execute(SEGMENT)
    for _ in range(40):  # 1.25 s: half of the leading joint's path
        station.tick()
    return station


def arm_data_hold(cause: str) -> Transition:
    return Transition(
        previous=Phase.S0_IDLE,
        phase=Phase.SAFE_HOLD,
        code="fsm.safe_hold.arm_data",
        params={"cause": cause},
        expected_next=Phase.S0_IDLE,
    )


def test_stale_arm_data_stops_the_segment_and_forces_safe_hold(clock) -> None:
    """REQ-MOT-024: data older than 0.15 s stops the arm and forces SAFE_HOLD."""
    station = idle_with_segment_half_done(clock)

    station.arm.simulate_stale_data()
    for _ in range(4):  # sample age up to 0.125 s
        assert station.tick() is None
    assert station.tick() == arm_data_hold("port.stale_data")

    station.arm.clear_simulated_failures()
    clock.advance(1.0)
    assert station.arm.read_state().progress == SegmentProgress(
        segment=SEGMENT, status=SegmentStatus.STOPPED, fraction=0.578125
    )


def test_lost_arm_link_forces_safe_hold_and_stops_once_the_link_is_back(
    clock,
) -> None:
    """REQ-MOT-024: a lost link forces SAFE_HOLD; the refused stop is sent again."""
    station = idle_with_segment_half_done(clock)

    station.arm.simulate_disconnect()
    assert station.tick() == arm_data_hold("port.disconnected")

    station.arm.clear_simulated_failures()
    assert station.tick() is None
    assert station.arm.read_state().progress == SegmentProgress(
        segment=SEGMENT, status=SegmentStatus.STOPPED, fraction=0.53125
    )


def test_adapter_fault_stops_the_segment_and_forces_safe_hold(clock) -> None:
    """REQ-MOT-024: a latched adapter fault stops the arm and forces SAFE_HOLD."""
    station = idle_with_segment_half_done(clock)

    station.arm.simulate_adapter_fault()

    assert station.tick() == arm_data_hold("port.adapter_fault")
    assert station.arm.read_state().progress == SegmentProgress(
        segment=SEGMENT, status=SegmentStatus.STOPPED, fraction=0.515625
    )


def test_arm_stopped_away_from_stow_keeps_safe_hold_on_full_evidence(clock) -> None:
    """REQ-MIS-017: with every check passing, SAFE_HOLD still needs the arm stowed."""
    station = idle_with_segment_half_done(clock)
    station.arm.simulate_adapter_fault()
    station.tick()
    station.arm.clear_simulated_failures()

    for _ in range(320):  # 10 s of trusted data and full evidence
        assert station.tick() is None

    assert station.machine.phase is Phase.SAFE_HOLD
    assert station.machine.failing_checks == ()
