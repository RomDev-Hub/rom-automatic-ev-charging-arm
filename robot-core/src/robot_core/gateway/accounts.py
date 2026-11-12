"""User accounts: name, roles and argon2id password hash, in one file on the device.

Only hashes are stored (REQ-AUTH-002), and no account exists until one is created
on the device (REQ-AUTH-003).
"""

import os
import re
import secrets
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from typing import Literal, Self

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from argon2.profiles import RFC_9106_LOW_MEMORY
from pydantic import BaseModel

USERS_FILE_NAME = "users.json"
USERNAME_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,64}")
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128

# RFC 9106 second recommendation (64 MiB, 3 passes, 4 lanes), above the OWASP
# minimum that REQ-AUTH-002 sets.
_HASHER = PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)


class Role(StrEnum):
    """Account roles of docs/requirements/gateway-config-data.md."""

    OPERATOR = "operator"
    MAINTAINER = "maintainer"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class Account:
    username: str
    roles: tuple[Role, ...]


class AccountError(ValueError):
    """An account that cannot be created as asked."""


class _UserRecord(BaseModel):
    username: str
    password_hash: str
    roles: list[Role]


class _UsersFile(BaseModel):
    version: Literal[1] = 1
    users: list[_UserRecord] = []


class AccountStore:
    """Accounts kept in one JSON file, replaced whole and atomically on each change."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def in_config_dir(cls, config_dir: Path) -> Self:
        return cls(config_dir / USERS_FILE_NAME)

    def verify(self, username: str, password: str) -> Account | None:
        """The account whose name and password these are; None for any mismatch.

        An unknown name costs one hash check like a known one, so the answer time
        does not tell which names exist.
        """
        record = self._find(username)
        password_hash = record.password_hash if record else self._decoy_hash
        try:
            _HASHER.verify(password_hash, _normalized(password))
        except VerificationError:
            return None
        return Account(record.username, tuple(record.roles)) if record else None

    def add(self, username: str, password: str, roles: Iterable[Role]) -> Account:
        """Create an account; a taken or malformed name and a weak password fail."""
        if not USERNAME_PATTERN.fullmatch(username):
            raise AccountError(
                "a username has 1 to 64 letters, digits, '.', '_' or '-'"
            )
        password = _normalized(password)
        if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
            raise AccountError(
                f"a password has {PASSWORD_MIN_LENGTH} to {PASSWORD_MAX_LENGTH}"
                " characters"
            )
        users = self._read()
        if any(user.username == username for user in users.users):
            raise AccountError(f"an account named {username!r} exists already")
        record = _UserRecord(
            username=username,
            password_hash=_HASHER.hash(password),
            roles=list(dict.fromkeys(roles)),
        )
        users.users.append(record)
        _replace_private_file(self.path, users.model_dump_json(indent=2) + "\n")
        return Account(record.username, tuple(record.roles))

    @cached_property
    def _decoy_hash(self) -> str:
        return _HASHER.hash(secrets.token_urlsafe(16))

    def _find(self, username: str) -> _UserRecord | None:
        return next(
            (user for user in self._read().users if user.username == username), None
        )

    def _read(self) -> _UsersFile:
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return _UsersFile()
        return _UsersFile.model_validate_json(text)


def _normalized(password: str) -> str:
    # One form for every way of typing the same characters (NIST SP 800-63B).
    return unicodedata.normalize("NFKC", password)


def _replace_private_file(path: Path, text: str) -> None:
    """Replace `path` atomically with a file only its owner may read or write."""
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
