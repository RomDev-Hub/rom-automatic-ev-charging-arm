"""Reject directories outside the agreed repository layout and stale .gitkeep placeholders.

A new directory is added by extending FIXED or OPEN here and recording it in ADR 0002.
"""

import subprocess
import sys
from collections import defaultdict

PLACEHOLDER = ".gitkeep"
ROBOT_CORE = "robot-core/src/robot_core"
ROBOT_CORE_PACKAGES = (
    "gateway",
    "mission",
    "motion",
    "arm",
    "perception",
    "calibration",
    "ports",
    "adapters",
    "config",
    "recording",
    "harvest",
    "ota",
    "defaults",
    "locales",
    "cli",
)
DOC_AREAS = (
    "decisions",
    "requirements",
    "safety",
    "architecture",
    "verification",
    "manual",
)

# Directories that must exist exactly as named; nothing may be added beside their listed children.
FIXED = {
    ".devcontainer",
    ".github",
    ".github/workflows",
    "contracts",
    "robot-core",
    "robot-core/src",
    ROBOT_CORE,
    "robot-core/tests",
    "operator-ui",
    "operator-ui/src",
    "training",
    "training/src",
    "deploy",
    "third_party",
    "docs",
    "scripts",
}

# Directories whose inner structure belongs to the code or content they hold.
OPEN = {
    "contracts/schemas",
    *(f"{ROBOT_CORE}/{package}" for package in ROBOT_CORE_PACKAGES),
    *(f"robot-core/tests/{tier}" for tier in ("unit", "integration", "sim", "hil")),
    *(f"operator-ui/src/{area}" for area in ("app", "features", "shared")),
    "training/src/training",
    "training/configs",
    *(f"deploy/{area}" for area in ("docker", "release", "host", "os", "site")),
    "datasets",
    "models",
    "third_party/licenses",
    *(f"docs/{area}" for area in DOC_AREAS),
}


def repo_paths() -> list[str]:
    listing = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    return [path for path in listing.split("\0") if path]


def is_allowed(directory: str) -> bool:
    if directory in FIXED or directory in OPEN:
        return True
    parts = directory.split("/")
    return any("/".join(parts[:depth]) in OPEN for depth in range(1, len(parts)))


def find_violations(paths: list[str]) -> list[str]:
    children: dict[str, set[str]] = defaultdict(set)
    directories: set[str] = set()
    for path in paths:
        parts = path.split("/")
        for depth in range(1, len(parts) + 1):
            children["/".join(parts[: depth - 1]) or "."].add(parts[depth - 1])
            if depth < len(parts):
                directories.add("/".join(parts[:depth]))
    problems = [
        f"directory not in the agreed layout: {d}/"
        for d in sorted(directories)
        if not is_allowed(d)
    ]
    problems += [
        f"remove {PLACEHOLDER}: {d}/ already has content"
        for d, names in sorted(children.items())
        if PLACEHOLDER in names and len(names) > 1
    ]
    return problems


def main() -> int:
    problems = find_violations(repo_paths())
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
