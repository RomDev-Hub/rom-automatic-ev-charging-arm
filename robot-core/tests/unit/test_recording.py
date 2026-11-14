"""MCAP recordings written on virtual clocks and read back with the mcap reader."""

import errno
import io
import json
import math
import os
from pathlib import Path

import pytest
from mcap.reader import make_reader

from robot_core.mission.machine import Phase, Reason, Transition
from robot_core.ports.arm import ArmState
from robot_core.recording.recorder import (
    Recorder,
    RecorderStatus,
    RecordingFault,
    recordings_dir,
)

RUN_ID = "7d3f2c9e"
START_NS = 1_794_472_800_000_000_000  # 2026-11-12T08:40:00Z
FILE_NAME = "20261112T084000Z_7d3f2c9e.mcap"
STOW_RAD = (0.0, -1.5708, 2.618, -1.0472, -1.5708, 0.0)
MEASURED_VALUES = {"type": "array", "items": {"type": ["number", "null"]}}
PHASE_CHANGED_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "description": "Mission phase change, with the data of the phaseChanged event.",
    "type": "object",
    "properties": {
        "previous": {"type": "string"},
        "phase": {"type": "string"},
        "code": {"type": "string"},
        "params": {
            "type": "object",
            "additionalProperties": {"type": ["string", "number", "boolean", "null"]},
        },
        "expected_next": {"type": ["string", "null"]},
    },
    "required": ["previous", "phase", "code", "params", "expected_next"],
    "additionalProperties": False,
}
ARM_STATE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "description": "Measured arm sample; null stands for a value that is not finite.",
    "type": "object",
    "properties": {
        "joint_position_rad": MEASURED_VALUES,
        "joint_velocity_rad_s": MEASURED_VALUES,
    },
    "required": ["joint_position_rad", "joint_velocity_rad_s"],
    "additionalProperties": False,
}
HOLD_ON_STALE_DATA = Transition(
    previous=Phase.S0_IDLE,
    phase=Phase.SAFE_HOLD,
    code=Reason.SAFE_HOLD_ARM_DATA,
    params={"cause": "port.stale_data"},
    expected_next=Phase.S0_IDLE,
)
ROOM_FOR_HEADER_BYTES = 64


class FullDisk(io.BytesIO):
    """File kept in memory, on a disk with `free_bytes` left; writing past them fails."""

    def __init__(self, free_bytes: int) -> None:
        super().__init__()
        self.free_bytes = free_bytes

    def write(self, data) -> int:
        if self.tell() + len(data) > self.free_bytes:
            raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))
        return super().write(data)


def stowed_sample(clock) -> ArmState:
    return ArmState(
        joint_position_rad=STOW_RAD,
        joint_velocity_rad_s=(0.0,) * len(STOW_RAD),
        measured_at_s=clock(),
        progress=None,
    )


def wall_clock(clock):
    """Host wall clock in ns, at START_NS now and moving with the virtual clock."""
    start_s = clock()
    return lambda: START_NS + round((clock() - start_s) * 1e9)


def open_recorder(clock, directory: Path, **seams) -> Recorder:
    return Recorder(
        RUN_ID,
        directory=directory,
        wall_clock_ns=wall_clock(clock),
        monotonic_s=clock,
        **seams,
    )


def strict_json(data: bytes):
    """Decode JSON as RFC 8259 defines it, without NaN or infinity."""

    def reject(constant: str):
        raise ValueError(f"{constant} is not JSON")

    return json.loads(data, parse_constant=reject)


def read_messages(path: Path) -> list:
    """(topic, log_time, publish_time, message) of every message, in log time order."""
    with path.open("rb") as stream:
        return [
            (
                channel.topic,
                message.log_time,
                message.publish_time,
                strict_json(message.data),
            )
            for _, channel, message in make_reader(stream).iter_messages()
        ]


def read_channels(path: Path) -> dict:
    """Topic: (message encoding, schema name, schema encoding, schema), from the summary."""
    with path.open("rb") as stream:
        summary = make_reader(stream).get_summary()
    schemas = summary.schemas
    return {
        channel.topic: (
            channel.message_encoding,
            schemas[channel.schema_id].name,
            schemas[channel.schema_id].encoding,
            strict_json(schemas[channel.schema_id].data),
        )
        for channel in summary.channels.values()
    }


def test_recordings_go_to_the_volume_unless_the_environment_names_a_directory(
    tmp_path: Path,
) -> None:
    """ADR 0007: the `ev-arm-recordings` volume, or EV_ARM_RECORDINGS_DIR when set."""
    volume = Path("/var/lib/ev-arm/recordings")
    assert recordings_dir({}) == volume
    assert recordings_dir({"EV_ARM_RECORDINGS_DIR": ""}) == volume
    assert recordings_dir({"EV_ARM_RECORDINGS_DIR": str(tmp_path)}) == tmp_path


def test_run_file_is_named_by_start_time_and_run_id(
    clock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-REC-005, REQ-REC-011, REQ-REC-013: one file, in EV_ARM_RECORDINGS_DIR."""
    directory = tmp_path / "recordings"
    monkeypatch.setenv("EV_ARM_RECORDINGS_DIR", str(directory))

    recorder = Recorder(RUN_ID, wall_clock_ns=wall_clock(clock), monotonic_s=clock)

    assert recorder.status == RecorderStatus(
        active=True,
        path=directory / FILE_NAME,
        messages_written=0,
        messages_dropped=0,
        fault=None,
    )
    recorder.close()
    assert recorder.status.active is False
    assert [path.name for path in directory.iterdir()] == [FILE_NAME]


def test_each_channel_is_json_with_its_json_schema(clock, tmp_path: Path) -> None:
    """REQ-REC-005, REQ-REC-006: event and arm channels, each with its JSON Schema."""
    open_recorder(clock, tmp_path).close()

    assert read_channels(tmp_path / FILE_NAME) == {
        "/events/phase_changed": (
            "json",
            "ev_arm.PhaseChanged",
            "jsonschema",
            PHASE_CHANGED_SCHEMA,
        ),
        "/arm/state": ("json", "ev_arm.ArmState", "jsonschema", ARM_STATE_SCHEMA),
    }


def test_phase_changes_carry_state_code_and_params_at_host_time(
    clock, tmp_path: Path
) -> None:
    """REQ-REC-006, REQ-REC-007: a phase change is published at its log time."""
    recorder = open_recorder(clock, tmp_path)
    clock.advance(0.25)
    recorder.record_transition(
        Transition(
            previous=Phase.SAFE_HOLD,
            phase=Phase.S0_IDLE,
            code=Reason.IDLE_AFTER_SAFE_HOLD,
            params={},
            expected_next=None,
        )
    )
    clock.advance(0.5)
    recorder.record_transition(HOLD_ON_STALE_DATA)
    recorder.close()

    assert read_messages(tmp_path / FILE_NAME) == [
        (
            "/events/phase_changed",
            START_NS + 250_000_000,
            START_NS + 250_000_000,
            {
                "previous": "SAFE_HOLD",
                "phase": "S0_IDLE",
                "code": "fsm.idle.after_safe_hold",
                "params": {},
                "expected_next": None,
            },
        ),
        (
            "/events/phase_changed",
            START_NS + 750_000_000,
            START_NS + 750_000_000,
            {
                "previous": "S0_IDLE",
                "phase": "SAFE_HOLD",
                "code": "fsm.safe_hold.arm_data",
                "params": {"cause": "port.stale_data"},
                "expected_next": "S0_IDLE",
            },
        ),
    ]


def test_arm_samples_are_published_at_their_measurement_time(
    clock, tmp_path: Path
) -> None:
    """REQ-REC-006: the monotonic measurement time is moved onto the host wall clock."""
    recorder = open_recorder(clock, tmp_path)
    clock.advance(1.0)
    recorder.record_arm_state(
        ArmState(
            joint_position_rad=STOW_RAD,
            joint_velocity_rad_s=(0.25, 0.0, 0.0, 0.0, 0.0, -0.5),
            measured_at_s=clock() - 0.125,
            progress=None,
        )
    )
    recorder.close()

    assert read_messages(tmp_path / FILE_NAME) == [
        (
            "/arm/state",
            START_NS + 1_000_000_000,
            START_NS + 875_000_000,
            {
                "joint_position_rad": [0.0, -1.5708, 2.618, -1.0472, -1.5708, 0.0],
                "joint_velocity_rad_s": [0.25, 0.0, 0.0, 0.0, 0.0, -0.5],
            },
        )
    ]


def test_non_finite_numbers_are_recorded_as_null(clock, tmp_path: Path) -> None:
    """REQ-REC-006: JSON has no NaN or infinity (RFC 8259); such a number becomes null."""
    recorder = open_recorder(clock, tmp_path)
    recorder.record_arm_state(
        ArmState(
            joint_position_rad=(0.5, math.nan),
            joint_velocity_rad_s=(math.inf, -math.inf),
            measured_at_s=clock(),
            progress=None,
        )
    )
    clock.advance(0.25)
    recorder.record_transition(
        Transition(
            previous=Phase.S0_IDLE,
            phase=Phase.SAFE_HOLD,
            code=Reason.SAFE_HOLD_ARM_DATA,
            params={"cause": "port.stale_data", "age_s": math.inf},
            expected_next=Phase.S0_IDLE,
        )
    )
    recorder.close()

    assert [message for *_, message in read_messages(tmp_path / FILE_NAME)] == [
        {"joint_position_rad": [0.5, None], "joint_velocity_rad_s": [None, None]},
        {
            "previous": "S0_IDLE",
            "phase": "SAFE_HOLD",
            "code": "fsm.safe_hold.arm_data",
            "params": {"cause": "port.stale_data", "age_s": None},
            "expected_next": "S0_IDLE",
        },
    ]


def test_file_reaching_the_size_cap_is_closed_whole_and_recording_stops(
    clock, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """REQ-REC-005, REQ-REC-010: the run's one file closes whole at its cap."""
    cap_bytes = 16_384
    recorder = open_recorder(clock, tmp_path, max_file_bytes=cap_bytes)
    sent = 0
    while recorder.status.active and sent < 100_000:
        recorder.record_arm_state(
            ArmState(
                joint_position_rad=STOW_RAD,
                joint_velocity_rad_s=(float(sent),) * len(STOW_RAD),
                measured_at_s=clock(),
                progress=None,
            )
        )
        sent += 1
    recorder.record_transition(HOLD_ON_STALE_DATA)
    recorder.record_arm_state(stowed_sample(clock))
    recorder.close()

    path = tmp_path / FILE_NAME
    assert list(tmp_path.iterdir()) == [path]
    assert cap_bytes <= path.stat().st_size < cap_bytes * 3 // 2
    assert [
        message["joint_velocity_rad_s"][0] for *_, message in read_messages(path)
    ] == [float(number) for number in range(sent)]
    assert recorder.status == RecorderStatus(
        active=False,
        path=path,
        messages_written=sent,
        messages_dropped=2,
        fault=RecordingFault(
            code="rec.file_full", params={"path": str(path), "limit_bytes": 16_384}
        ),
    )
    assert [
        (record.levelname, "rec.file_full" in record.getMessage())
        for record in caplog.records
        if record.name == "robot_core.recording.recorder"
    ] == [("WARNING", True)]


def test_read_only_directory_leaves_recording_off_with_a_coded_fault(
    clock, tmp_path: Path
) -> None:
    """REQ-REC-011: the file cannot be created; recording and closing raise nothing."""

    def create_on_read_only_file_system(path: Path):
        raise OSError(errno.EROFS, os.strerror(errno.EROFS), str(path))

    recorder = open_recorder(
        clock, tmp_path, create_file=create_on_read_only_file_system
    )
    recorder.record_transition(HOLD_ON_STALE_DATA)
    recorder.record_arm_state(stowed_sample(clock))
    recorder.close()

    path = tmp_path / FILE_NAME
    assert recorder.status == RecorderStatus(
        active=False,
        path=path,
        messages_written=0,
        messages_dropped=2,
        fault=RecordingFault(
            code="rec.open_failed", params={"path": str(path), "cause": "EROFS"}
        ),
    )


def test_full_disk_stops_recording_with_a_coded_fault(clock, tmp_path: Path) -> None:
    """REQ-REC-011: the write that finds the disk full stops recording, raising nothing."""
    disk = FullDisk(ROOM_FOR_HEADER_BYTES)
    recorder = open_recorder(clock, tmp_path, create_file=lambda path: disk)
    sent = 0
    while recorder.status.active and sent < 100_000:
        recorder.record_arm_state(stowed_sample(clock))
        sent += 1
    recorder.record_transition(HOLD_ON_STALE_DATA)
    recorder.close()

    path = tmp_path / FILE_NAME
    assert recorder.status == RecorderStatus(
        active=False,
        path=path,
        messages_written=sent - 1,
        messages_dropped=2,
        fault=RecordingFault(
            code="rec.write_failed", params={"path": str(path), "cause": "ENOSPC"}
        ),
    )
    assert disk.closed


def test_full_disk_at_close_is_reported_with_a_coded_fault(
    clock, tmp_path: Path
) -> None:
    """REQ-REC-011: a summary that finds the disk full is reported; close raises nothing."""
    disk = FullDisk(ROOM_FOR_HEADER_BYTES)
    recorder = open_recorder(clock, tmp_path, create_file=lambda path: disk)
    recorder.record_transition(HOLD_ON_STALE_DATA)
    recorder.close()

    path = tmp_path / FILE_NAME
    assert recorder.status == RecorderStatus(
        active=False,
        path=path,
        messages_written=1,
        messages_dropped=0,
        fault=RecordingFault(
            code="rec.write_failed", params={"path": str(path), "cause": "ENOSPC"}
        ),
    )
    assert disk.closed
