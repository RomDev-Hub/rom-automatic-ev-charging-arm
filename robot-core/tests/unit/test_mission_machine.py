"""Mission state machine through its public methods, on a virtual clock."""

from robot_core.mission.machine import MissionMachine, Phase, Transition


def test_boot_ends_in_safe_hold_expecting_idle(clock) -> None:
    """REQ-MIS-013, REQ-MIS-005, REQ-MIS-003: BOOT goes to SAFE_HOLD, never idle."""
    machine = MissionMachine(clock)
    assert machine.phase is Phase.BOOT

    transition = machine.complete_boot()

    assert transition == Transition(
        previous=Phase.BOOT,
        phase=Phase.SAFE_HOLD,
        code="fsm.boot.ready",
        params={},
        expected_next=Phase.S0_IDLE,
    )
    assert machine.phase is Phase.SAFE_HOLD
    assert machine.expected_next is Phase.S0_IDLE


def test_time_in_phase_follows_the_injected_clock(clock) -> None:
    """REQ-MIS-006, REQ-MIS-004: time in phase comes from the injected clock."""
    machine = MissionMachine(clock)
    clock.advance(2.5)
    assert machine.time_in_phase_s == 2.5

    machine.complete_boot()
    assert machine.time_in_phase_s == 0.0

    clock.advance(0.25)
    assert machine.time_in_phase_s == 0.25
