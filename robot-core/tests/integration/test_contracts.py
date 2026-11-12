"""Gateway answers against the files of contracts/, their single source."""

import json
from pathlib import Path

import pytest

from robot_core.gateway.problems import ProblemCode, problem_response

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"
ERROR_CATALOGUE = json.loads(
    (CONTRACTS / "schemas" / "error-codes.schema.json").read_text(encoding="utf-8")
)


def catalogue_entry(code: str) -> dict:
    entries = (
        entry
        for group in ERROR_CATALOGUE["$defs"].values()
        for entry in group["oneOf"]
        if entry["const"] == code
    )
    return next(entries)


@pytest.mark.parametrize("code", list(ProblemCode))
def test_problem_details_follow_the_error_catalogue(code) -> None:
    """REQ-GW-014: type, status and title of each problem come from the catalogue."""
    entry = catalogue_entry(code)

    problem = json.loads(problem_response(code).body)

    assert problem == {
        "type": ERROR_CATALOGUE["x-problem-type"].format(code=code),
        "status": entry["x-http-status"],
        "title": entry["x-text"]["en"],
        "code": code,
        "params": {},
    }
