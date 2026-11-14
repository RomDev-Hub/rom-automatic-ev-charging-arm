"""Interfaces through which domain modules reach devices (docs/architecture/ports.md).

Domain modules call ports, never adapters; this package is a public contract.
"""

from dataclasses import dataclass
from enum import StrEnum


class PortCode(StrEnum):
    """Port codes from contracts/schemas/error-codes.schema.json."""

    DISCONNECTED = "port.disconnected"
    STALE_DATA = "port.stale_data"
    ADAPTER_FAULT = "port.adapter_fault"
    DIMENSION_MISMATCH = "port.dimension_mismatch"


@dataclass(frozen=True, slots=True)
class Refusal:
    """A command the port did not pass on to the device, with its stable code."""

    code: PortCode
