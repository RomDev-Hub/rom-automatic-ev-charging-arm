"""Settings of the gateway process."""

from dataclasses import dataclass
from pathlib import Path

# Mount point of the ev-arm-config volume in the container (ADR 0007).
DEFAULT_CONFIG_DIR = Path("/var/lib/ev-arm/config")


@dataclass(frozen=True, slots=True, kw_only=True)
class Settings:
    """Settings of the gateway.

    Attributes:
        config_dir: Directory of the station configuration and the user accounts.
    """

    config_dir: Path = DEFAULT_CONFIG_DIR
