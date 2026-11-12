"""Settings of the gateway process, from the EV_ARM_* environment variables."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Self

# Mount point of the ev-arm-config volume in the container (ADR 0007).
DEFAULT_CONFIG_DIR = Path("/var/lib/ev-arm/config")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


@dataclass(frozen=True, slots=True, kw_only=True)
class Settings:
    """Settings of the gateway; each one is listed in deploy/.env.example.

    Attributes:
        config_dir: Directory of the station configuration and the user accounts.
        host: Address that `serve` listens on.
        port: TCP port that `serve` listens on.
    """

    config_dir: Path = DEFAULT_CONFIG_DIR
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT

    @classmethod
    def from_environ(cls, environ: Mapping[str, str]) -> Self:
        """Read EV_ARM_CONFIG_DIR, EV_ARM_HOST and EV_ARM_PORT, where set."""
        port = environ.get("EV_ARM_PORT", str(DEFAULT_PORT))
        if not (port.isdigit() and 0 < int(port) < 65536):
            raise ValueError(f"EV_ARM_PORT is not a TCP port: {port!r}")
        return cls(
            config_dir=Path(environ.get("EV_ARM_CONFIG_DIR", DEFAULT_CONFIG_DIR)),
            host=environ.get("EV_ARM_HOST", DEFAULT_HOST),
            port=int(port),
        )
