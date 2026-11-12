"""Commands over REST; each one's lifecycle goes out on the push channel."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from robot_core.gateway.events import CommandState
from robot_core.gateway.problems import ProblemCode, ProblemError, problem_responses
from robot_core.gateway.runtime import CoreRuntime
from robot_core.gateway.sessions import SessionStore
from robot_core.mission.machine import Phase

logger = logging.getLogger(__name__)

STOP = "stop"
# Result codes belong to the command's requirements, not to the error catalogue.
STOP_ENGAGED = "cmd.stop.engaged"


class CommandResult(BaseModel):
    """Result of a command the core carried out (REQ-GW-013).

    Attributes:
        command_id: Tags the command's lifecycle messages on /api/ws (REQ-GW-007).
        phase: Phase of the mission machine once the command was handled.
    """

    command_id: str
    command: str
    code: str
    params: dict[str, Any]
    phase: Phase


def command_routes(runtime: CoreRuntime, sessions: SessionStore) -> APIRouter:
    router = APIRouter(dependencies=[Depends(sessions)])

    @router.post(
        "/api/commands/stop",
        responses=problem_responses(ProblemCode.AUTH_REQUIRED, ProblemCode.INTERNAL),
    )
    async def stop() -> CommandResult:
        """Stop: the arm stops at once, then the machine enters SAFE_STOP.

        An operational stop through software, not a safety function: the safety
        functions are hardware (ADR 0005, REQ-MIS-066). Only a restart leaves
        SAFE_STOP until the resume command exists.
        """
        command_id = str(uuid.uuid7())
        events = runtime.events
        events.publish_command(command_id, STOP, CommandState.PENDING)
        # Stop takes no parameter and is allowed in every phase: its checks pass.
        events.publish_command(command_id, STOP, CommandState.ACCEPTED)
        try:
            runtime.request_stop()
        except Exception:
            logger.exception("command %s %s failed", STOP, command_id)
            events.publish_command(
                command_id, STOP, CommandState.REJECTED, code=ProblemCode.INTERNAL
            )
            raise ProblemError(ProblemCode.INTERNAL) from None
        events.publish_command(
            command_id, STOP, CommandState.COMPLETED, code=STOP_ENGAGED
        )
        return CommandResult(
            command_id=command_id,
            command=STOP,
            code=STOP_ENGAGED,
            params={},
            phase=runtime.machine.phase,
        )

    @router.post("/api/commands/{command}", include_in_schema=False)
    async def unknown_command(command: str) -> None:
        """A command outside the contract (REQ-GW-012)."""
        raise ProblemError(ProblemCode.UNKNOWN_COMMAND, {"command": command})

    return router
