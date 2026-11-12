"""Push channel /api/ws: session handshake, phase changes, command lifecycles."""

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


def test_stop_answers_its_command_id_and_the_lifecycle_follows_on_the_channel(
    client, credentials, evidence
) -> None:
    """REQ-GW-007, REQ-GW-013, REQ-MIS-066: accepted, SAFE_STOP, then completed."""
    client.post("/api/session", json=credentials)

    with client.websocket_connect(PUSH_URL) as websocket:
        evidence.update(EVERY_CHECK_PASSES)
        assert receive(websocket)["data"]["phase"] == "S0_IDLE"
        response = client.post("/api/commands/stop")
        messages = [receive(websocket) for _ in range(4)]

    assert response.status_code == 200
    result = response.json()
    command_id = result.pop("command_id")
    assert result == {
        "command": "stop",
        "code": "cmd.stop.engaged",
        "params": {},
        "phase": "SAFE_STOP",
    }
    lifecycle = {"command_id": command_id, "command": "stop"}
    assert [message["data"] for message in messages] == [
        {**lifecycle, "state": "pending"},
        {**lifecycle, "state": "accepted"},
        {
            "previous": "S0_IDLE",
            "phase": "SAFE_STOP",
            "code": "fsm.safe_stop.stop_command",
            "params": {},
            "expected_next": "S0_IDLE",
        },
        {**lifecycle, "state": "completed", "code": "cmd.stop.engaged", "params": {}},
    ]
    assert [message["type"].rsplit(".", 2)[-2] for message in messages] == [
        "command",
        "command",
        "phase",
        "command",
    ]
    sequences = [int(message["sequence"]) for message in messages]
    assert sequences == list(range(sequences[0], sequences[0] + 4))


def test_stop_in_safe_stop_completes_without_a_phase_change(
    client, credentials
) -> None:
    """REQ-MIS-066: a second Stop stops again and completes, with no phase change."""
    client.post("/api/session", json=credentials)

    with client.websocket_connect(PUSH_URL) as websocket:
        client.post("/api/commands/stop")
        first = [receive(websocket) for _ in range(4)]
        response = client.post("/api/commands/stop")
        second = [receive(websocket)["data"] for _ in range(3)]

    assert first[2]["data"]["phase"] == "SAFE_STOP"
    assert response.json()["phase"] == "SAFE_STOP"
    assert [data["state"] for data in second] == ["pending", "accepted", "completed"]
    assert second[2]["code"] == "cmd.stop.engaged"


def test_command_failing_inside_answers_500_and_is_rejected_on_the_channel(
    client, credentials, runtime, monkeypatch, caplog
) -> None:
    """REQ-GW-015: internal error, never `cmd.bad_params`; logged with traceback."""

    def failing_stop() -> None:
        raise RuntimeError("supervisor unavailable")

    monkeypatch.setattr(runtime, "request_stop", failing_stop)
    client.post("/api/session", json=credentials)

    with client.websocket_connect(PUSH_URL) as websocket:
        response = client.post("/api/commands/stop")
        messages = [receive(websocket) for _ in range(3)]

    assert response.status_code == 500
    assert response.json()["code"] == "err.internal"
    [pending, accepted, rejected] = [message["data"] for message in messages]
    assert (pending["state"], accepted["state"]) == ("pending", "accepted")
    assert rejected == {
        "command_id": pending["command_id"],
        "command": "stop",
        "state": "rejected",
        "code": "err.internal",
        "params": {},
    }
    [record] = [r for r in caplog.records if r.name == "robot_core.gateway.commands"]
    assert record.exc_info is not None


def test_stop_needs_a_session(client) -> None:
    """REQ-AUTH-006: no session, no command."""
    response = client.post("/api/commands/stop")

    assert response.status_code == 401
    assert response.json()["code"] == "err.auth.required"


def test_command_outside_the_contract_is_refused(client, credentials) -> None:
    """REQ-GW-012: `cmd.unknown`, so a client tells it from a refused command."""
    client.post("/api/session", json=credentials)

    response = client.post("/api/commands/self_destruct")

    assert response.status_code == 404
    assert response.json()["code"] == "cmd.unknown"
    assert response.json()["params"] == {"command": "self_destruct"}


def test_a_message_from_the_client_closes_the_channel(client, credentials) -> None:
    """REQ-GW-006: the channel takes no command; a client that sends one is cut off."""
    client.post("/api/session", json=credentials)

    with client.websocket_connect(PUSH_URL) as websocket:
        websocket.send_json({"command": "stop"})
        with pytest.raises(WebSocketDisconnect) as closed:
            receive(websocket)

    assert closed.value.code == 1008
