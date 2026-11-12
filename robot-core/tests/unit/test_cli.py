"""Command line: `admin create` takes the password from a prompt or stdin only."""

import io

import pytest

from robot_core.cli.main import main
from robot_core.gateway.accounts import Account, AccountStore, Role

PASSWORD = "correct horse battery staple"


class Terminal(io.StringIO):
    """Standard input attached to a terminal."""

    def isatty(self) -> bool:
        return True


@pytest.fixture
def config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("EV_ARM_CONFIG_DIR", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize("prefix", ["", "﻿"], ids=["plain", "byte-order-mark"])
def test_admin_create_reads_the_password_from_stdin(
    config_dir, monkeypatch, prefix
) -> None:
    """REQ-CLI-006, REQ-AUTH-003: the first admin is created on the device.

    A byte order mark before the password, as Windows PowerShell 5.1 pipes it, is
    not part of the password.
    """
    monkeypatch.setattr("sys.stdin", io.StringIO(prefix + PASSWORD + "\n"))

    status = main(["admin", "create", "admin"])

    assert status == 0
    accounts = AccountStore.in_config_dir(config_dir)
    assert accounts.verify("admin", PASSWORD) == Account("admin", (Role.ADMIN,))


@pytest.mark.parametrize(
    ("typed", "status"),
    [((PASSWORD, PASSWORD), 0), ((PASSWORD, "correct horse battery stable"), 1)],
    ids=["confirmed", "mistyped"],
)
def test_admin_create_asks_twice_on_a_terminal(
    config_dir, monkeypatch, capsys, typed, status
) -> None:
    """REQ-CLI-006: on a terminal the password is asked twice, without echo."""
    answers = iter(typed)
    monkeypatch.setattr("sys.stdin", Terminal())
    monkeypatch.setattr("getpass.getpass", lambda prompt: next(answers))

    assert main(["admin", "create", "admin"]) == status

    created = AccountStore.in_config_dir(config_dir).verify("admin", PASSWORD)
    assert (created is not None) == (status == 0)
    assert ("passwords differ" in capsys.readouterr().err) == (status == 1)


def test_admin_create_needs_an_existing_configuration_directory(
    tmp_path, monkeypatch, capsys
) -> None:
    """The command never creates the configuration directory itself."""
    missing = tmp_path / "missing"
    monkeypatch.setenv("EV_ARM_CONFIG_DIR", str(missing))
    monkeypatch.setattr("sys.stdin", io.StringIO(PASSWORD + "\n"))

    assert main(["admin", "create", "admin"]) == 1

    assert "EV_ARM_CONFIG_DIR" in capsys.readouterr().err
    assert not missing.exists()
