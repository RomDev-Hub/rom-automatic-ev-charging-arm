"""Error answers as RFC 9457 problem details, coded from the error catalogue.

contracts/schemas/error-codes.schema.json is the single source of the codes: the
status and title of each code below repeat its `x-http-status` and `x-text.en`, and a
test keeps the two equal.
"""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Any, cast

from fastapi import FastAPI, Request, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

MEDIA_TYPE = "application/problem+json"
PROBLEM_TYPE = "tag:romdev-hub.github.io,2026:ev-arm/problems/{code}"


class ProblemCode(StrEnum):
    """Catalogue codes the gateway answers with."""

    AUTH_REQUIRED = "err.auth.required"
    INVALID_CREDENTIALS = "err.auth.invalid_credentials"
    NOT_FOUND = "err.not_found"
    INTERNAL = "err.internal"
    NOT_READY = "err.not_ready"
    BAD_PARAMS = "cmd.bad_params"
    UNKNOWN_COMMAND = "cmd.unknown"


_STATUS_AND_TITLE: Mapping[ProblemCode, tuple[int, str]] = MappingProxyType(
    {
        ProblemCode.AUTH_REQUIRED: (401, "Not signed in or the session has expired"),
        ProblemCode.INVALID_CREDENTIALS: (401, "Incorrect username or password"),
        ProblemCode.NOT_FOUND: (404, "Requested resource not found"),
        ProblemCode.INTERNAL: (500, "Internal system error"),
        ProblemCode.NOT_READY: (503, "System not ready"),
        ProblemCode.BAD_PARAMS: (
            422,
            "Command parameters missing, mistyped or out of range",
        ),
        ProblemCode.UNKNOWN_COMMAND: (404, "Command not defined in the contract"),
    }
)


class Problem(BaseModel):
    """Problem details (RFC 9457) with the catalogue code and its parameters."""

    type: str
    status: int
    title: str
    code: ProblemCode
    params: dict[str, Any]


class ProblemError(Exception):
    """Raised by a route to answer with the problem details of a catalogue code."""

    def __init__(
        self, code: ProblemCode, params: Mapping[str, object] | None = None
    ) -> None:
        super().__init__(code)
        self.code = code
        self.params = dict(params or {})


def problem_response(
    code: ProblemCode, params: Mapping[str, object] | None = None
) -> JSONResponse:
    """Problem details of `code`, sent with the status the catalogue gives it."""
    status, title = _STATUS_AND_TITLE[code]
    problem = Problem(
        type=PROBLEM_TYPE.format(code=code),
        status=status,
        title=title,
        code=code,
        params=dict(params or {}),
    )
    return JSONResponse(
        problem.model_dump(mode="json"), status_code=status, media_type=MEDIA_TYPE
    )


def problem_responses(*codes: ProblemCode) -> dict[int | str, dict[str, Any]]:
    """OpenAPI entries of the problem details a route can answer with."""
    by_status: dict[int, list[str]] = {}
    for code in codes:
        status, title = _STATUS_AND_TITLE[code]
        by_status.setdefault(status, []).append(f"`{code}`: {title}")
    content = {MEDIA_TYPE: {"schema": {"$ref": "#/components/schemas/Problem"}}}
    return {
        status: {"description": "; ".join(lines), "content": content}
        for status, lines in by_status.items()
    }


def problem_schemas() -> dict[str, Any]:
    """OpenAPI component schemas of the Problem model and its definitions."""
    schema = Problem.model_json_schema(ref_template="#/components/schemas/{model}")
    return {**schema.pop("$defs", {}), "Problem": schema}


def install_problem_handlers(app: FastAPI) -> None:
    """Answer every error of the REST API with problem details (REQ-GW-014)."""
    app.add_exception_handler(ProblemError, _raised_problem)
    app.add_exception_handler(RequestValidationError, _invalid_request)
    app.add_exception_handler(HTTPException, _routing_error)
    app.add_exception_handler(Exception, _unexpected_error)


async def _raised_problem(request: Request, error: Exception) -> Response:
    problem = cast(ProblemError, error)
    return problem_response(problem.code, problem.params)


async def _invalid_request(request: Request, error: Exception) -> Response:
    # Locations only: a rejected value can be a secret such as a password.
    errors = cast(RequestValidationError, error).errors()
    fields = sorted({".".join(map(str, item["loc"])) for item in errors})
    return problem_response(ProblemCode.BAD_PARAMS, {"fields": fields})


async def _routing_error(request: Request, error: Exception) -> Response:
    # No route, or no method of the route, matches: the resource is not found.
    http_error = cast(HTTPException, error)
    if http_error.status_code in (404, 405):
        return problem_response(ProblemCode.NOT_FOUND)
    return await http_exception_handler(request, http_error)


async def _unexpected_error(request: Request, error: Exception) -> Response:
    # The server logs the traceback; the answer carries none (REQ-GW-014).
    return problem_response(ProblemCode.INTERNAL)
