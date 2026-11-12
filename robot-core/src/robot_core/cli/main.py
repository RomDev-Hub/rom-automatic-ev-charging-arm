"""Entry point `robot-core`: `serve` runs the core, `admin create` adds an admin."""

import argparse
import getpass
import os
import sys
from collections.abc import Sequence

import uvicorn

from robot_core.gateway.accounts import AccountError, AccountStore, Role
from robot_core.gateway.app import create_app
from robot_core.gateway.settings import Settings


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command named in `argv`; returns the exit status."""
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        settings = Settings.from_environ(os.environ)
    except ValueError as error:
        parser.error(str(error))
    status: int = arguments.run(arguments, settings)
    return status


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="robot-core",
        description="On-device control core of the automatic EV charging arm.",
    )
    commands = parser.add_subparsers(required=True, metavar="command")
    serve = commands.add_parser(
        "serve",
        help="run the REST API, the push channel and the supervision loop",
        description="Listen on EV_ARM_HOST and EV_ARM_PORT.",
    )
    serve.set_defaults(run=_serve)
    admin = commands.add_parser("admin", help="manage accounts")
    admin_commands = admin.add_subparsers(required=True, metavar="command")
    create = admin_commands.add_parser(
        "create",
        help="create an account with the admin role",
        description=(
            "Create an admin account in EV_ARM_CONFIG_DIR. The password is asked"
            " twice on a terminal, or read as one line from standard input."
        ),
    )
    create.add_argument("username")
    create.set_defaults(run=_create_admin)
    return parser


def _serve(arguments: argparse.Namespace, settings: Settings) -> int:
    """Run the gateway and its supervision loop until stopped (REQ-CLI-001)."""
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)
    return 0


def _create_admin(arguments: argparse.Namespace, settings: Settings) -> int:
    """Create an admin account on the device (REQ-CLI-006, REQ-AUTH-003)."""
    if not settings.config_dir.is_dir():
        print(
            f"no configuration directory at {settings.config_dir};"
            " create it or set EV_ARM_CONFIG_DIR",
            file=sys.stderr,
        )
        return 1
    accounts = AccountStore.in_config_dir(settings.config_dir)
    try:
        accounts.add(arguments.username, _read_password(), [Role.ADMIN])
    except AccountError as error:
        print(f"no account created: {error}", file=sys.stderr)
        return 1
    print(f"created the admin account {arguments.username!r}", file=sys.stderr)
    return 0


def _read_password() -> str:
    # Never from the command line, where shell history and ps would show it.
    if not sys.stdin.isatty():
        # Windows PowerShell 5.1 starts piped text with a byte order mark.
        return sys.stdin.readline().removeprefix("﻿").rstrip("\r\n")
    password = getpass.getpass("Password: ")
    if getpass.getpass("Repeat the password: ") != password:
        raise AccountError("the two passwords differ")
    return password
