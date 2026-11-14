"""Session login over HTTPS: the cookie, the account behind it, logout, refusals."""

import pytest
from fastapi.testclient import TestClient

from robot_core.gateway.app import create_app
from robot_core.gateway.settings import Settings

PROBLEMS = "tag:romdev-hub.github.io,2026:ev-arm/problems/"


def session_cookie(response) -> tuple[str, set[str]]:
    """Value and lower-cased attributes of the session cookie a response sets."""
    name_value, *attributes = (
        part.strip() for part in response.headers["set-cookie"].split(";")
    )
    name, _, value = name_value.partition("=")
    assert name == "__Host-id"
    return value, {attribute.lower() for attribute in attributes}


def read_session_with(client, token):
    """GET /api/session sending only the given session identifier."""
    client.cookies.clear()
    return client.get("/api/session", headers={"cookie": f"__Host-id={token}"})


def test_login_sets_a_secure_cookie_and_the_session_names_the_account(
    client, credentials
) -> None:
    """REQ-AUTH-004, REQ-AUTH-008: Secure, HttpOnly, SameSite=Strict, host-bound."""
    response = client.post("/api/session", json=credentials)

    assert response.status_code == 200
    assert response.json() == {"username": "admin", "roles": ["admin"]}
    _, attributes = session_cookie(response)
    assert attributes == {"httponly", "path=/", "samesite=strict", "secure"}
    assert client.get("/api/session").json() == {
        "username": "admin",
        "roles": ["admin"],
    }


def test_each_login_opens_a_new_session_and_ends_the_replaced_one(
    client, credentials
) -> None:
    """REQ-AUTH-004: a new identifier at every login, against session fixation."""
    first, _ = session_cookie(client.post("/api/session", json=credentials))
    second, _ = session_cookie(client.post("/api/session", json=credentials))

    assert second != first
    assert read_session_with(client, first).status_code == 401
    assert read_session_with(client, second).status_code == 200


def test_logout_ends_the_session_on_the_server_and_clears_the_cookie(
    client, credentials
) -> None:
    """REQ-AUTH-004: logging out ends the session on the server."""
    token, _ = session_cookie(client.post("/api/session", json=credentials))

    response = client.delete("/api/session")

    assert response.status_code == 204
    cleared, attributes = session_cookie(response)
    assert cleared == '""'
    assert "max-age=0" in attributes
    assert read_session_with(client, token).status_code == 401


@pytest.mark.parametrize("method", ["GET", "DELETE"])
def test_session_routes_need_a_session(client, method) -> None:
    """REQ-AUTH-006: no valid session, 401 problem details `err.auth.required`."""
    response = client.request(method, "/api/session")

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": PROBLEMS + "err.auth.required",
        "status": 401,
        "title": "Not signed in or the session has expired",
        "code": "err.auth.required",
        "params": {},
    }


@pytest.mark.parametrize(
    "mistake",
    [{"password": "not the password at all"}, {"username": "nobody"}],
    ids=["wrong-password", "unknown-user"],
)
def test_login_with_wrong_credentials_opens_no_session(
    client, credentials, mistake
) -> None:
    """REQ-AUTH-004: one answer for a wrong password and an unknown name."""
    response = client.post("/api/session", json={**credentials, **mistake})

    assert response.status_code == 401
    assert response.json()["code"] == "err.auth.invalid_credentials"
    assert "set-cookie" not in response.headers


def test_credentials_in_the_url_open_no_session(client, credentials) -> None:
    """REQ-AUTH-005: the login reads its body, never the query string."""
    response = client.post("/api/session", params=credentials)

    assert response.status_code == 422
    assert response.json()["code"] == "cmd.bad_params"
    assert response.json()["params"] == {"fields": ["body"]}
    assert "set-cookie" not in response.headers


def test_no_account_exists_until_one_is_created(tmp_path, credentials) -> None:
    """REQ-AUTH-003: with no account file, nobody can log in."""
    client = TestClient(create_app(Settings(config_dir=tmp_path)))

    response = client.post("/api/session", json=credentials)

    assert response.status_code == 401
    assert response.json()["code"] == "err.auth.invalid_credentials"


def test_unreadable_accounts_file_answers_internal_error_without_details(
    tmp_path, credentials
) -> None:
    """REQ-GW-014: 500 problem details, with no traceback or internal detail."""
    (tmp_path / "users.json").write_text("{not json", encoding="utf-8")
    client = TestClient(
        create_app(Settings(config_dir=tmp_path)), raise_server_exceptions=False
    )

    response = client.post("/api/session", json=credentials)

    assert response.status_code == 500
    assert response.json() == {
        "type": PROBLEMS + "err.internal",
        "status": 500,
        "title": "Internal system error",
        "code": "err.internal",
        "params": {},
    }
