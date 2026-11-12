"""Importing robot_core leaves the process and the machine as it found them."""

import contextlib
import importlib
import json
import logging
import os
import subprocess
import sys
from collections.abc import Iterator, MutableMapping
from typing import Any
from unittest import mock

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
FILESYSTEM_EVENTS = frozenset(
    {
        "os.link",
        "os.mkdir",
        "os.remove",
        "os.rename",
        "os.rmdir",
        "os.symlink",
        "os.truncate",
    }
)


class RecordingEnviron(MutableMapping[str, str]):
    """Stand-in for os.environ that logs every access."""

    def __init__(self, real: MutableMapping[str, str], log: list[str]) -> None:
        self._real = real
        self._log = log

    def __getitem__(self, key: str) -> str:
        self._log.append(f"environment read: {key}")
        return self._real[key]

    def __setitem__(self, key: str, value: str) -> None:
        self._log.append(f"environment write: {key}")
        self._real[key] = value

    def __delitem__(self, key: str) -> None:
        self._log.append(f"environment write: {key}")
        del self._real[key]

    def __iter__(self) -> Iterator[str]:
        self._log.append("environment read: all variables")
        return iter(self._real)

    def __len__(self) -> int:
        return len(self._real)

    def copy(self) -> dict[str, str]:
        self._log.append("environment read: all variables")
        return dict(self._real)


def is_side_effect(event: str, args: tuple[Any, ...]) -> bool:
    """Tell whether an audit event writes to disk, uses a socket or starts a thread."""
    if event == "open":
        return bool(args[2] & WRITE_FLAGS)
    return event in FILESYSTEM_EVENTS or event.startswith(("socket.", "_thread.start"))


def logging_state() -> dict[str, tuple[int, int]]:
    loggers = {"": logging.getLogger(), **logging.Logger.manager.loggerDict}
    return {
        name: (logger.level, len(logger.handlers))
        for name, logger in loggers.items()
        if isinstance(logger, logging.Logger)
    }


class SideEffectBlocked(BaseException):
    """Stops a side effect; not an Exception, so `except Exception` cannot hide it."""


def import_side_effects() -> list[str]:
    """Import robot_core in this interpreter and describe every side effect."""
    side_effects: list[str] = []
    importing = True

    def block(event: str, args: tuple[Any, ...]) -> None:
        if importing and is_side_effect(event, args):
            side_effects.append(f"{event}: {args!r}")
            raise SideEffectBlocked(event)

    sys.addaudithook(block)
    logging_before = logging_state()
    environ = RecordingEnviron(os.environ, side_effects)
    with (
        contextlib.suppress(SideEffectBlocked),
        mock.patch.object(os, "environ", environ),
    ):
        importlib.import_module("robot_core")
    importing = False
    unconfigured = (logging.NOTSET, 0)
    side_effects += [
        f"logging configured: {name or 'root'}"
        for name, state in logging_state().items()
        if state != logging_before.get(name, unconfigured)
    ]
    return side_effects


def test_import_has_no_side_effects() -> None:
    # -I: ignore PYTHON* variables and keep the working directory off sys.path.
    # -B: write no bytecode cache, which the audit hook would report as a write.
    child = subprocess.run(
        [sys.executable, "-I", "-B", __file__],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == []


if __name__ == "__main__":
    print(json.dumps(import_side_effects()))
