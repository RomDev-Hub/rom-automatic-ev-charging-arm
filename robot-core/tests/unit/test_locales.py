"""The two locale files, the single source of every displayed string (REQ-I18N-001).

They are read from the installed package, so the test also covers what ships.
"""

import json
import re
from importlib.resources import files

LOCALES = files("robot_core") / "locales"
PARAMETER = re.compile(r"\{(\w+)\}")


def messages(language: str) -> dict[str, str]:
    text = (LOCALES / f"{language}.json").read_text(encoding="utf-8")
    loaded: dict[str, str] = json.loads(text)
    return loaded


def test_both_locales_have_the_same_keys() -> None:
    """REQ-I18N-002: no key exists in one language only."""
    assert sorted(messages("vi")) == sorted(messages("en"))


def test_each_key_takes_the_same_parameters_in_both_locales() -> None:
    """REQ-I18N-002: a `{name}` parameter is filled the same way in vi and en."""
    vi, en = messages("vi"), messages("en")
    differing = {
        key: (PARAMETER.findall(vi[key]), PARAMETER.findall(en[key]))
        for key in vi.keys() & en.keys()
        if set(PARAMETER.findall(vi[key])) != set(PARAMETER.findall(en[key]))
    }

    assert differing == {}
