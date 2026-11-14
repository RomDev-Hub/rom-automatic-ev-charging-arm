"""Health route, answered from the live state of the supervision runtime."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from robot_core.gateway.problems import ProblemCode, ProblemError, problem_responses
from robot_core.gateway.runtime import CoreRuntime


class HealthReport(BaseModel):
    """Every health check passes."""

    status: Literal["ok"]


def health_routes(runtime: CoreRuntime) -> APIRouter:
    router = APIRouter()

    @router.get("/api/health", responses=problem_responses(ProblemCode.NOT_READY))
    async def read_health() -> HealthReport:
        """Answer 200 while every health check passes, else 503 naming the failing.

        The checks: the supervision loop ticked within the last second, the arm port
        is connected with fresh data and no latched fault, and the kinematics library
        is loaded. No session is needed and no operating data is returned
        (REQ-GW-023).
        """
        failing = runtime.failing_health_checks()
        if failing:
            raise ProblemError(ProblemCode.NOT_READY, {"failing": failing})
        return HealthReport(status="ok")

    return router
