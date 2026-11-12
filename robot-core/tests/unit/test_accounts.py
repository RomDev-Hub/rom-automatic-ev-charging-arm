"""Account store: argon2id hashes in a private file, and the accounts it refuses."""

import json
import stat
import sys
import unicodedata

import pytest
from argon2 import Type, extract_parameters

from robot_core.gateway.accounts import Account, AccountError, AccountStore, Role

PASSWORD = "mật khẩu đủ dài"


def test_stored_password_is_an_argon2id_hash_above_the_owasp_minimum(
    tmp_path,
) -> None:
    """REQ-AUTH-002: argon2id with at least 19 MiB, 2 passes, 1 lane; no plain text."""
    store = AccountStore.in_config_dir(tmp_path)

    store.add("admin", PASSWORD, [Role.ADMIN])

    text = (tmp_path / "users.json").read_text(encoding="utf-8")
    [user] = json.loads(text)["users"]
    parameters = extract_parameters(user["password_hash"])
    assert parameters.type is Type.ID
    assert parameters.memory_cost >= 19 * 1024
    assert parameters.time_cost >= 2
    assert parameters.parallelism >= 1
    assert PASSWORD not in text
    assert store.verify("admin", PASSWORD) == Account("admin", (Role.ADMIN,))


def test_password_typed_in_another_unicode_form_still_verifies(tmp_path) -> None:
    """The same characters typed precomposed or decomposed are one password."""
    store = AccountStore.in_config_dir(tmp_path)
    store.add("admin", unicodedata.normalize("NFC", PASSWORD), [Role.ADMIN])

    account = store.verify("admin", unicodedata.normalize("NFD", PASSWORD))

    assert account == Account("admin", (Role.ADMIN,))


@pytest.mark.skipif(sys.platform == "win32", reason="Windows has no POSIX file mode")
def test_accounts_file_is_private_to_its_owner(tmp_path) -> None:
    AccountStore.in_config_dir(tmp_path).add("admin", PASSWORD, [Role.ADMIN])

    assert stat.S_IMODE((tmp_path / "users.json").stat().st_mode) == 0o600


@pytest.mark.parametrize(
    ("username", "password", "reason"),
    [
        ("admin", PASSWORD, "exists already"),
        ("operator", "too short", "12 to 128 characters"),
        ("two words", PASSWORD, "a username has"),
    ],
    ids=["taken-name", "short-password", "malformed-name"],
)
def test_account_that_cannot_exist_is_refused(
    tmp_path, username, password, reason
) -> None:
    store = AccountStore.in_config_dir(tmp_path)
    store.add("admin", PASSWORD, [Role.ADMIN])

    with pytest.raises(AccountError, match=reason):
        store.add(username, password, [Role.OPERATOR])

    users = json.loads((tmp_path / "users.json").read_text(encoding="utf-8"))["users"]
    assert [user["username"] for user in users] == ["admin"]
