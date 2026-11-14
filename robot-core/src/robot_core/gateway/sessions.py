"""Login sessions, kept on the server and carried by the session cookie."""

import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, Security
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from robot_core.gateway.accounts import (
    PASSWORD_MAX_LENGTH,
    Account,
    AccountStore,
    Role,
)
from robot_core.gateway.problems import ProblemCode, ProblemError, problem_responses

# The __Host- prefix ties the cookie to this host and to path / (OWASP).
COOKIE_NAME = "__Host-id"
_cookie = APIKeyCookie(name=COOKIE_NAME, scheme_name="session", auto_error=False)


@dataclass(frozen=True, slots=True)
class Session:
    token: str
    account: Account


class SessionStore:
    """Open sessions, in memory, so a restart ends them all.

    Used as a FastAPI dependency, it gives the request's session, or answers 401
    with `err.auth.required` when the request has none (REQ-AUTH-006).
    """

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def open(self, account: Account) -> Session:
        """A session with a new identifier from a CSPRNG (REQ-AUTH-004)."""
        session = Session(token=secrets.token_urlsafe(32), account=account)
        self._sessions[session.token] = session
        return session

    def find(self, token: str | None) -> Session | None:
        return self._sessions.get(token) if token is not None else None

    def close(self, token: str | None) -> None:
        if token is not None:
            self._sessions.pop(token, None)

    async def __call__(
        self, token: Annotated[str | None, Security(_cookie)]
    ) -> Session:
        session = self.find(token)
        if session is None:
            raise ProblemError(ProblemCode.AUTH_REQUIRED)
        return session


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class SessionInfo(BaseModel):
    """The account of the session, without any secret (REQ-AUTH-008)."""

    username: str
    roles: list[Role]


def session_routes(accounts: AccountStore, sessions: SessionStore) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/api/session",
        responses=problem_responses(
            ProblemCode.INVALID_CREDENTIALS, ProblemCode.BAD_PARAMS
        ),
    )
    async def open_session(
        credentials: Credentials, request: Request, response: Response
    ) -> SessionInfo:
        """Log in, and receive the session cookie.

        The cookie is Secure, HttpOnly and SameSite=Strict, with a new identifier
        each time (REQ-AUTH-004). Credentials travel in the body, never in the URL
        (REQ-AUTH-005).
        """
        account = await run_in_threadpool(
            accounts.verify, credentials.username, credentials.password
        )
        if account is None:
            raise ProblemError(ProblemCode.INVALID_CREDENTIALS)
        sessions.close(request.cookies.get(COOKIE_NAME))
        session = sessions.open(account)
        response.set_cookie(
            COOKIE_NAME, session.token, secure=True, httponly=True, samesite="strict"
        )
        return _info(account)

    @router.get("/api/session", responses=problem_responses(ProblemCode.AUTH_REQUIRED))
    async def read_session(
        session: Annotated[Session, Depends(sessions)],
    ) -> SessionInfo:
        """The account and roles of the current session."""
        return _info(session.account)

    @router.delete(
        "/api/session",
        status_code=204,
        responses=problem_responses(ProblemCode.AUTH_REQUIRED),
    )
    async def close_session(
        session: Annotated[Session, Depends(sessions)], response: Response
    ) -> None:
        """Log out: the session ends on the server and the cookie is cleared."""
        sessions.close(session.token)
        response.delete_cookie(
            COOKIE_NAME, secure=True, httponly=True, samesite="strict"
        )

    return router


def _info(account: Account) -> SessionInfo:
    return SessionInfo(username=account.username, roles=list(account.roles))
