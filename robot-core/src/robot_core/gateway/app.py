"""Application factory of the gateway; nothing runs before the app's lifespan."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from robot_core.gateway.accounts import AccountStore
from robot_core.gateway.health import health_routes
from robot_core.gateway.problems import install_problem_handlers, problem_schemas
from robot_core.gateway.runtime import CoreRuntime
from robot_core.gateway.sessions import SessionStore, session_routes
from robot_core.gateway.settings import Settings

API_TITLE = "robot-core REST API"
# Version of the REST contract, not of the software; a draft until it is agreed.
API_VERSION = "0.1.0-draft"


class _GatewayApp(FastAPI):
    def openapi(self) -> dict[str, Any]:
        document = super().openapi()
        components = document.setdefault("components", {})
        components.setdefault("schemas", {}).update(problem_schemas())
        return document


def create_app(
    settings: Settings | None = None, *, runtime: CoreRuntime | None = None
) -> FastAPI:
    """Build the gateway around a runtime, by default the simulated station.

    Building touches no device, writes no file and starts no task: the runtime starts
    with the app's lifespan and stops with it (REQ-GW-020, REQ-GW-022).
    """
    settings = settings if settings is not None else Settings()
    core = runtime if runtime is not None else CoreRuntime()
    sessions = SessionStore()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await core.start()
        try:
            yield
        finally:
            await core.stop()

    app = _GatewayApp(
        title=API_TITLE,
        version=API_VERSION,
        lifespan=lifespan,
        # Only login and health may answer without a session (REQ-AUTH-006), so the
        # generated documentation is not served; contracts/openapi.json is.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        # Telemetry leaves the device only through the project's settings (ADR 0016).
        telemetry={"auto_configure": False},
    )
    install_problem_handlers(app)
    app.include_router(health_routes(core))
    accounts = AccountStore.in_config_dir(settings.config_dir)
    app.include_router(session_routes(accounts, sessions))
    return app
