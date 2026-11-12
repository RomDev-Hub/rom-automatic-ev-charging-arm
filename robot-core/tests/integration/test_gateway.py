"""Gateway app over HTTP: lifespan, health and problem details for errors."""

import logging
import time
from collections.abc import Iterator, Mapping

import pytest
from fastapi.testclient import TestClient

from robot_core.arm.kinematics import KinematicsUnavailableError
from robot_core.gateway.app import create_app
from robot_core.gateway.runtime import CoreRuntime
from robot_core.mission.machine import ChecklistItem

NOT_READY = "tag:romdev-hub.github.io,2026:ev-arm/problems/err.not_ready"


def kinematics_loaded() -> None:
    """Probe of a platform where Pinocchio loads."""


def kinematics_missing() -> None:
    raise KinematicsUnavailableError("Pinocchio cannot be imported")


class BreakableEvidence(Mapping[ChecklistItem, bool | None]):
    """No evidence, until reading it fails the way a faulty source would."""

    def __init__(self) -> None:
        self.broken = False

    def __getitem__(self, item: ChecklistItem) -> bool | None:
        raise KeyError(item)

    def __iter__(self) -> Iterator[ChecklistItem]:
        if self.broken:
            raise RuntimeError("evidence source failed")
        return iter(())

    def __len__(self) -> int:
        return 0


def test_health_is_ok_while_loop_arm_port_and_kinematics_are_sound() -> None:
    """REQ-GW-022, REQ-GW-023: the loop has ticked before the first request."""
    runtime = CoreRuntime(kinematics_probe=kinematics_loaded)

    with TestClient(create_app(runtime=runtime)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_names_the_arm_port_when_its_link_is_lost() -> None:
    """REQ-GW-023: 503 problem details naming the failing check."""
    runtime = CoreRuntime(kinematics_probe=kinematics_loaded)

    with TestClient(create_app(runtime=runtime)) as client:
        runtime.arm.simulate_disconnect()
        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": NOT_READY,
        "status": 503,
        "title": "System not ready",
        "code": "err.not_ready",
        "params": {"failing": ["arm_port"]},
    }


def test_health_names_kinematics_when_the_library_cannot_load() -> None:
    """REQ-GW-023: the app still starts, and health says what is missing."""
    runtime = CoreRuntime(kinematics_probe=kinematics_missing)

    with TestClient(create_app(runtime=runtime)) as client:
        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json()["params"] == {"failing": ["kinematics"]}


def test_health_names_the_supervision_loop_once_it_stops_ticking(caplog) -> None:
    """REQ-GW-023: a loop that died shows in health within a second, and in the log."""
    evidence = BreakableEvidence()
    runtime = CoreRuntime(
        checklist_evidence=evidence, kinematics_probe=kinematics_loaded
    )

    with TestClient(create_app(runtime=runtime)) as client:
        evidence.broken = True
        deadline_s = time.monotonic() + 3.0
        while (response := client.get("/api/health")).status_code == 200:
            assert time.monotonic() < deadline_s, "health still ok"
            time.sleep(0.05)

    assert response.json()["params"] == {"failing": ["supervision_loop"]}
    assert (
        "robot_core.gateway.runtime",
        logging.ERROR,
        "supervision loop stopped",
    ) in (caplog.record_tuples)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/nothing"),
        ("POST", "/api/health"),
        ("GET", "/docs"),
        ("GET", "/redoc"),
        ("GET", "/openapi.json"),
    ],
)
def test_paths_outside_the_contract_answer_not_found(method, path) -> None:
    """REQ-GW-014, REQ-AUTH-006: no route beyond the contract, documentation included."""
    client = TestClient(
        create_app(runtime=CoreRuntime(kinematics_probe=kinematics_loaded))
    )

    response = client.request(method, path)

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "err.not_found"
