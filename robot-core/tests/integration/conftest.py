"""Fixtures of the gateway tests: an account on disk, an app and its HTTPS client."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from robot_core.gateway.accounts import AccountStore, Role
from robot_core.gateway.app import create_app
from robot_core.gateway.runtime import CoreRuntime
from robot_core.gateway.settings import Settings


def kinematics_loaded() -> None:
    """Probe of a platform where Pinocchio loads."""


@pytest.fixture(scope="session")
def credentials() -> dict[str, str]:
    return {"username": "admin", "password": "correct horse battery staple"}


@pytest.fixture(scope="session")
def config_dir(tmp_path_factory, credentials) -> Path:
    directory = tmp_path_factory.mktemp("config")
    AccountStore.in_config_dir(directory).add(
        credentials["username"], credentials["password"], [Role.ADMIN]
    )
    return directory


@pytest.fixture
def runtime() -> CoreRuntime:
    return CoreRuntime(kinematics_probe=kinematics_loaded)


@pytest.fixture
def client(config_dir, runtime) -> Iterator[TestClient]:
    # HTTPS, so that the client sends the Secure session cookie back.
    app = create_app(Settings(config_dir=config_dir), runtime=runtime)
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client
