"""Push channel /api/ws: handshake by session cookie, phase changes in sequence."""

import re
from concurrent.futures import ThreadPoolExecutor

import pytest
from starlette.testclient import WebSocketDenialResponse
from starlette.websockets import WebSocketDisconnect

from robot_core.gateway.runtime import CoreRuntime
from robot_core.mission.machine import ChecklistItem

PUSH_URL = "wss://testserver/api/ws"
RECEIVE_TIMEOUT_S = 5.0
EVERY_CHECK_PASSES = dict.fromkeys(ChecklistItem, True)


def receive(websocket) -> dict:
    """Next message of the channel; fails instead of hanging when none comes."""
    reader = ThreadPoolExecutor(max_workers=1)
    try:
        return reader.submit(websocket.receive_json).result(RECEIVE_TIMEOUT_S)
    finally:
        reader.shutdown(wait=False)


@pytest.fixture
def evidence() -> dict:
    return {}


@pytest.fixture
def runtime(evidence) -> CoreRuntime:
    return CoreRuntime(checklist_evidence=evidence, kinematics_probe=lambda: None)


@pytest.mark.parametrize(
    "query", ["", "?id={token}"], ids=["no-session", "session-id-in-url"]
)
def test_handshake_without_the_session_cookie_is_refused_before_upgrade(
    client, credentials, query
) -> None:
    """REQ-AUTH-006, REQ-AUTH-005: 401 problem details instead of a connection."""
    client.post("/api/session", json=credentials)
    token = client.cookies["__Host-id"]
    client.cookies.clear()

    with (
        pytest.raises(WebSocketDenialResponse) as denial,
        client.websocket_connect(PUSH_URL + query.format(token=token)),
    ):
        pass

    assert denial.value.status_code == 401
    assert denial.value.json()["code"] == "err.auth.required"


def test_phase_changes_are_pushed_as_they_happen_in_sequence(
    client, credentials, evidence, runtime
) -> None:
    """REQ-GW-002, REQ-GW-005, REQ-GW-008: CloudEvents envelope with sequence."""
    client.post("/api/session", json=credentials)

    with client.websocket_connect(PUSH_URL) as websocket:
        evidence.update(EVERY_CHECK_PASSES)
        idle = receive(websocket)
        runtime.arm.simulate_disconnect()
        hold = receive(websocket)

    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z", idle.pop("time"))
    assert idle.pop("id") != hold.pop("id")
    assert idle == {
        "specversion": "1.0",
        "source": f"/core/{runtime.run_id}",
        "type": "io.github.romdev-hub.ev-arm.phase.changed",
        "sequence": "00000000000000000002",  # BOOT to SAFE_HOLD was the first
        "data": {
            "previous": "SAFE_HOLD",
            "phase": "S0_IDLE",
            "code": "fsm.idle.after_safe_hold",
            "params": {},
            "expected_next": None,
        },
    }
    assert hold["sequence"] == "00000000000000000003"
    assert hold["data"] == {
        "previous": "S0_IDLE",
        "phase": "SAFE_HOLD",
        "code": "fsm.safe_hold.arm_data",
        "params": {"cause": "port.disconnected"},
        "expected_next": "S0_IDLE",
    }


def test_a_message_from_the_client_closes_the_channel(client, credentials) -> None:
    """REQ-GW-006: the channel takes no command; a client that sends one is cut off."""
    client.post("/api/session", json=credentials)

    with client.websocket_connect(PUSH_URL) as websocket:
        websocket.send_json({"command": "stop"})
        with pytest.raises(WebSocketDisconnect) as closed:
            receive(websocket)

    assert closed.value.code == 1008
