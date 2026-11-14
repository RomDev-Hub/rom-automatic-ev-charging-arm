"""Telemetry snapshot, the payload of telemetrySnapshot in contracts/asyncapi.yaml.

Only the phase block is built so far; every other block is reported unavailable
(REQ-GW-017) until the module that owns it provides it.
"""

from collections.abc import Callable
from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from robot_core.gateway.problems import ProblemCode, ProblemError, problem_responses
from robot_core.gateway.sessions import SessionStore
from robot_core.mission.machine import MissionMachine, Phase, Transition

BLOCK_UNAVAILABLE = "err.telemetry.block_unavailable"


class PhaseNote(BaseModel):
    """Reason code and parameters of the latest phase change."""

    code: str
    params: dict[str, Any]


class PhaseBlock(BaseModel):
    """Current phase and the latest phase change (REQ-MIS-004)."""

    phase: Phase
    previous: Phase
    expected_next: Phase | None
    since_s: float = Field(
        ge=0, description="Time in the current phase (s), on the monotonic clock."
    )
    note: PhaseNote


class BlockUnavailable(BaseModel):
    """A block that could not be built (REQ-GW-017)."""

    unavailable: Literal[True] = True
    code: str = BLOCK_UNAVAILABLE


class TelemetryData(BaseModel):
    """One telemetry snapshot (REQ-GW-016), alike on /api/ws and over REST."""

    data_origin: Literal["measured", "simulated"]
    phase: PhaseBlock | BlockUnavailable
    safe_hold: BlockUnavailable
    supervision: BlockUnavailable
    session: BlockUnavailable
    lot: BlockUnavailable
    motion: BlockUnavailable
    devices: BlockUnavailable
    perception: BlockUnavailable
    sim_faults: BlockUnavailable
    health: BlockUnavailable
    build: BlockUnavailable


_UNAVAILABLE_BLOCKS = tuple(
    name
    for name, field in TelemetryData.model_fields.items()
    if field.annotation is BlockUnavailable
)


def build_snapshot(machine: MissionMachine, latest: Transition) -> TelemetryData:
    """Snapshot of the simulated station, from the machine and its latest change."""
    phase = PhaseBlock(
        phase=machine.phase,
        previous=latest.previous,
        expected_next=machine.expected_next,
        since_s=machine.time_in_phase_s,
        note=PhaseNote(code=latest.code, params=dict(latest.params)),
    )
    return TelemetryData.model_validate(
        {
            "data_origin": "simulated",
            "phase": phase,
            **dict.fromkeys(_UNAVAILABLE_BLOCKS, BlockUnavailable()),
        }
    )


def telemetry_routes(
    latest_snapshot: Callable[[], TelemetryData | None], sessions: SessionStore
) -> APIRouter:
    router = APIRouter(dependencies=[Depends(sessions)])

    @router.get(
        "/api/telemetry",
        responses=problem_responses(ProblemCode.AUTH_REQUIRED, ProblemCode.NOT_READY),
    )
    async def read_telemetry() -> TelemetryData:
        """The latest telemetry snapshot, as pushed on /api/ws (REQ-GW-019)."""
        snapshot = latest_snapshot()
        if snapshot is None:
            raise ProblemError(ProblemCode.NOT_READY)
        return snapshot

    return router
