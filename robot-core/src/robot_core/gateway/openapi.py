"""Write contracts/openapi.json, the REST contract, from the gateway app itself.

From robot-core: uv run python -m robot_core.gateway.openapi ../contracts/openapi.json
"""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from robot_core.gateway.app import create_app


def render() -> str:
    """OpenAPI document of the gateway, as committed in contracts/openapi.json."""
    document = create_app().openapi()
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Write the OpenAPI document of the robot-core REST API."
    )
    parser.add_argument("output", type=Path, help="normally contracts/openapi.json")
    arguments = parser.parse_args(argv)
    arguments.output.write_text(render(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
