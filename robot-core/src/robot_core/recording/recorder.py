"""Recording of phase changes and arm samples into an MCAP file of the run.

mcap.writer is imported when a file is opened, not when this module is imported: the
zstd codec it loads reads the environment at import, and importing robot_core stays
free of side effects.
"""

import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from mcap.well_known import MessageEncoding, SchemaEncoding

from robot_core.mission.machine import Transition
from robot_core.ports.arm import ArmState
from robot_core.recording.channels import (
    ARM_STATE,
    CHANNELS,
    PHASE_CHANGED,
    ChannelSpec,
    encode_arm_state,
    encode_transition,
)

if TYPE_CHECKING:
    from mcap.writer import Writer

RECORDINGS_DIR_VARIABLE = "EV_ARM_RECORDINGS_DIR"
DEFAULT_RECORDINGS_DIR = Path("/var/lib/ev-arm/recordings")
NS_PER_S = 1_000_000_000


def recordings_dir(environ: Mapping[str, str] = os.environ) -> Path:
    """Directory of the recordings: `EV_ARM_RECORDINGS_DIR` when set, else the
    `ev-arm-recordings` volume (ADR 0007)."""
    return Path(environ.get(RECORDINGS_DIR_VARIABLE) or DEFAULT_RECORDINGS_DIR)


def _create_file(path: Path) -> BinaryIO:
    """Create `path` and its missing parent directories; never replace a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("xb")


@dataclass(frozen=True, slots=True)
class _OpenFile:
    path: Path
    stream: BinaryIO
    writer: Writer
    channel_ids: Mapping[str, int]


class Recorder:
    """Records phase changes and arm samples into an MCAP file of the run (REQ-REC-005).

    Every channel is JSON with a JSON Schema. `log_time` is the host wall clock when a
    message is recorded; `publish_time` is the time of its source: the measurement of an
    arm sample, moved from the host monotonic clock onto the wall clock, or `log_time`
    for a phase change, which has no time of its own (REQ-REC-006).

    Messages are written in the caller's thread, and an instance is not thread-safe.
    """

    def __init__(
        self,
        run_id: str,
        *,
        directory: Path | None = None,
        wall_clock_ns: Callable[[], int] = time.time_ns,
        monotonic_s: Callable[[], float] = time.monotonic,
        create_file: Callable[[Path], BinaryIO] = _create_file,
    ) -> None:
        """Open the run's file in `directory`, by default `recordings_dir()`.

        The file is named by its UTC start time and the run ID (REQ-REC-013).
        """
        self._run_id = run_id
        self._directory = recordings_dir() if directory is None else directory
        self._wall_clock_ns = wall_clock_ns
        self._monotonic_s = monotonic_s
        self._create_file = create_file
        self._file: _OpenFile | None = self._open_file()

    def record_transition(self, transition: Transition) -> None:
        """Record a phase change (REQ-REC-007)."""
        log_time_ns = self._wall_clock_ns()
        message = encode_transition(transition)
        self._write(PHASE_CHANGED, message, log_time_ns, log_time_ns)

    def record_arm_state(self, state: ArmState) -> None:
        """Record an arm sample, published at the time it was measured."""
        log_time_ns = self._wall_clock_ns()
        age_ns = round(state.age_s(self._monotonic_s()) * NS_PER_S)
        message = encode_arm_state(state)
        self._write(ARM_STATE, message, log_time_ns, log_time_ns - age_ns)

    def close(self) -> None:
        """Write the summary and close the file; later records are ignored."""
        file, self._file = self._file, None
        if file is not None:
            file.writer.finish()  # type: ignore[no-untyped-call]
            file.stream.close()

    def _open_file(self) -> _OpenFile:
        import mcap.writer

        start = datetime.fromtimestamp(self._wall_clock_ns() // NS_PER_S, UTC)
        path = self._directory / f"{start:%Y%m%dT%H%M%SZ}_{self._run_id}.mcap"
        stream = self._create_file(path)
        writer = mcap.writer.Writer(stream)
        writer.start()
        channel_ids = {}
        for channel in CHANNELS:
            schema_id = writer.register_schema(
                channel.schema_name,
                SchemaEncoding.JSONSchema,
                json.dumps(channel.schema).encode(),
            )
            channel_ids[channel.topic] = writer.register_channel(
                channel.topic, MessageEncoding.JSON, schema_id
            )
        return _OpenFile(path, stream, writer, channel_ids)

    def _write(
        self,
        channel: ChannelSpec,
        message: bytes,
        log_time_ns: int,
        publish_time_ns: int,
    ) -> None:
        file = self._file
        if file is None:
            return
        file.writer.add_message(
            channel_id=file.channel_ids[channel.topic],
            log_time=log_time_ns,
            data=message,
            publish_time=publish_time_ns,
        )
