"""Mission state machine through its public methods, on a virtual clock."""

import pytest

from robot_core.mission.machine import (
    ChecklistItem,
    MissionMachine,
    Phase,
    Reason,
    Snapshot,
    Transition,
)

REQUIRED_CHECKS = (
    "chk.motion_port",
    "chk.kinematics",
    "chk.collision",
    "chk.camera",
    "chk.calib",
    "chk.estop",
    "chk.safety_level",
)
ALL_PASS = {ChecklistItem(code): True for code in REQUIRED_CHECKS}


def evidence(checklist=ALL_PASS, *, arm_stowed=True, arm_data_fault=None) -> Snapshot:
    return Snapshot(
        checklist=checklist, arm_stowed=arm_stowed, arm_data_fault=arm_data_fault
    )


def holding(clock) -> MissionMachine:
    machine = MissionMachine(clock)
    machine.complete_boot()
    return machine


def idle(clock) -> MissionMachine:
    machine = holding(clock)
    machine.step(evidence())
    return machine


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


@pytest.mark.parametrize(
    "checklist",
    [
        {**ALL_PASS, ChecklistItem.CALIB: False},
        {**ALL_PASS, ChecklistItem.CALIB: None},
        {item: True for item in ALL_PASS if item is not ChecklistItem.CALIB},
    ],
    ids=["failing", "unknown", "missing"],
)
def test_safe_hold_waits_while_a_check_fails_or_lacks_data(clock, checklist) -> None:
    """REQ-MIS-015, REQ-MIS-017: a failing, unknown or missing check keeps the hold."""
    machine = holding(clock)

    assert machine.step(evidence(checklist)) is None
    assert machine.phase is Phase.SAFE_HOLD
    assert machine.failing_checks == ("chk.calib",)


def test_safe_hold_never_ends_on_elapsed_time(clock) -> None:
    """REQ-MIS-017: no amount of waiting replaces the evidence."""
    machine = holding(clock)

    for _ in range(1000):
        clock.advance(1.0)
        assert machine.step(evidence({})) is None

    assert machine.phase is Phase.SAFE_HOLD
    assert machine.failing_checks == REQUIRED_CHECKS


def test_safe_hold_ends_in_idle_once_every_check_passes_with_arm_stowed(
    clock,
) -> None:
    """REQ-MIS-017: the full checklist with the arm at its stow pose ends the hold."""
    machine = holding(clock)

    transition = machine.step(evidence())

    assert transition == Transition(
        previous=Phase.SAFE_HOLD,
        phase=Phase.S0_IDLE,
        code="fsm.idle.after_safe_hold",
        params={},
        expected_next=None,
    )
    assert machine.phase is Phase.S0_IDLE


@pytest.mark.parametrize("arm_stowed", [False, None], ids=["away", "unknown"])
def test_safe_hold_waits_while_the_arm_is_not_known_to_be_stowed(
    clock, arm_stowed
) -> None:
    """REQ-MIS-017: S0_IDLE follows SAFE_HOLD only with the arm at its stow pose."""
    machine = holding(clock)

    assert machine.step(evidence(arm_stowed=arm_stowed)) is None
    assert machine.phase is Phase.SAFE_HOLD
    assert machine.failing_checks == ()


@pytest.mark.parametrize(
    ("start", "previous"),
    [(MissionMachine, Phase.BOOT), (idle, Phase.S0_IDLE)],
    ids=["BOOT", "S0_IDLE"],
)
def test_any_phase_can_be_forced_into_safe_hold(clock, start, previous) -> None:
    """REQ-MIS-003: a forced hold carries its code; every check fails again."""
    machine = start(clock)

    transition = machine.force_safe_hold(
        Reason.SAFE_HOLD_ARM_DATA, {"cause": "port.stale_data"}
    )

    assert transition == Transition(
        previous=previous,
        phase=Phase.SAFE_HOLD,
        code="fsm.safe_hold.arm_data",
        params={"cause": "port.stale_data"},
        expected_next=Phase.S0_IDLE,
    )
    assert machine.failing_checks == REQUIRED_CHECKS


def test_forcing_safe_hold_while_holding_records_no_transition(clock) -> None:
    """REQ-MIS-002: staying in SAFE_HOLD is no phase change."""
    machine = holding(clock)
    clock.advance(5.0)

    transition = machine.force_safe_hold(
        Reason.SAFE_HOLD_ARM_DATA, {"cause": "port.stale_data"}
    )

    assert transition is None
    assert machine.phase is Phase.SAFE_HOLD
    assert machine.time_in_phase_s == 5.0


def test_untrusted_arm_data_forces_safe_hold_with_its_cause(clock) -> None:
    """REQ-MOT-024: untrusted arm data takes S0_IDLE to SAFE_HOLD."""
    machine = idle(clock)

    transition = machine.step(evidence(arm_data_fault="port.disconnected"))

    assert transition == Transition(
        previous=Phase.S0_IDLE,
        phase=Phase.SAFE_HOLD,
        code="fsm.safe_hold.arm_data",
        params={"cause": "port.disconnected"},
        expected_next=Phase.S0_IDLE,
    )


def test_untrusted_arm_data_keeps_safe_hold_despite_full_evidence(clock) -> None:
    """REQ-MOT-024: SAFE_HOLD does not end on arm data that cannot be trusted."""
    machine = holding(clock)

    assert machine.step(evidence(arm_data_fault="port.stale_data")) is None
    assert machine.phase is Phase.SAFE_HOLD
