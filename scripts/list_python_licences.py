"""List the licence of every package locked in a uv.lock, read from its PyPI metadata.

Prints one line per locked package, then a GitHub Actions warning for each licence missing from ALLOWED_LICENCES, the JSON list that .github/workflows/ci.yaml shares with its npm licence step.
Usage: python scripts/list_python_licences.py robot-core/uv.lock
"""

import json
import os
import sys
import tomllib
import urllib.request
from collections import defaultdict

# PyPI metadata of these releases says BSD-3-Clause, but the LICENSE file they ship, upstream Pinocchio at tag v4.1.0, is BSD-2-Clause (ADR 0012).
OVERRIDES = {
    ("pin", "4.1.0"): "BSD-2-Clause",
    ("libpinocchio", "4.1.0"): "BSD-2-Clause",
}


def pypi_licence(name: str, version: str) -> str:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    with urllib.request.urlopen(url, timeout=30) as response:
        info = json.load(response)["info"]
    if info.get("license_expression"):
        return info["license_expression"]
    text = (info.get("license") or "").strip()
    if text and "\n" not in text:
        return text
    classifiers = [
        classifier.rsplit(" :: ", 1)[-1]
        for classifier in info.get("classifiers") or []
        if classifier.startswith("License :: ")
    ]
    return " / ".join(classifiers) or "UNKNOWN"


def main() -> int:
    allowed = set(json.loads(os.environ["ALLOWED_LICENCES"]))
    with open(sys.argv[1], "rb") as lock:
        locked = [
            (package["name"], package["version"])
            for package in tomllib.load(lock)["package"]
            if "registry" in package["source"]
        ]
    names_by_licence: defaultdict[str, list[str]] = defaultdict(list)
    for name, version in locked:
        licence = OVERRIDES.get((name, version)) or pypi_licence(name, version)
        print(f"{name} {version}: {licence}")
        names_by_licence[licence].append(name)
    for licence, names in sorted(names_by_licence.items()):
        if licence not in allowed:
            print(f"::warning::licence {licence}: {', '.join(names)}")
    for name, version in sorted(OVERRIDES.keys() - set(locked)):
        print(
            f"::warning::licence override for {name} {version} matches no locked package; read the LICENSE file of the locked version"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
