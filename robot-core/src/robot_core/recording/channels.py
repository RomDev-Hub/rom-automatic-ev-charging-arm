"""Channels of a recording: topics, JSON Schemas and the JSON of each message.

A phase change carries the fields of the phaseChanged event of contracts/asyncapi.yaml
(REQ-REC-007); the MCAP record itself carries the time, so the message holds no
envelope.
"""

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass

from robot_core.mission.machine import ParamValue, Transition
from robot_core.ports.arm import ArmState

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

_MEASURED_VALUES = {"type": "array", "items": {"type": ["number", "null"]}}


@dataclass(frozen=True, slots=True)
class ChannelSpec:
    """A recorded channel: its topic, and the name and JSON Schema of its messages."""

    topic: str
    schema_name: str
    schema: Mapping[str, object]


PHASE_CHANGED = ChannelSpec(
    topic="/events/phase_changed",
    schema_name="ev_arm.PhaseChanged",
    schema={
        "$schema": JSON_SCHEMA_DIALECT,
        "description": "Mission phase change, with the data of the phaseChanged event.",
        "type": "object",
        "properties": {
            "previous": {"type": "string"},
            "phase": {"type": "string"},
            "code": {"type": "string"},
            "params": {
                "type": "object",
                "additionalProperties": {
                    "type": ["string", "number", "boolean", "null"]
                },
            },
            "expected_next": {"type": ["string", "null"]},
        },
        "required": ["previous", "phase", "code", "params", "expected_next"],
        "additionalProperties": False,
    },
)

ARM_STATE = ChannelSpec(
    topic="/arm/state",
    schema_name="ev_arm.ArmState",
    schema={
        "$schema": JSON_SCHEMA_DIALECT,
        "description": "Measured arm sample; null stands for a value that is not finite.",
        "type": "object",
        "properties": {
            "joint_position_rad": _MEASURED_VALUES,
            "joint_velocity_rad_s": _MEASURED_VALUES,
        },
        "required": ["joint_position_rad", "joint_velocity_rad_s"],
        "additionalProperties": False,
    },
)

CHANNELS = (PHASE_CHANGED, ARM_STATE)


def encode_transition(transition: Transition) -> bytes:
    """Message of a phase change on PHASE_CHANGED."""
    return _encode(
        {
            "previous": transition.previous,
            "phase": transition.phase,
            "code": transition.code,
            "params": {
                key: _finite_or_null(value) for key, value in transition.params.items()
            },
            "expected_next": transition.expected_next,
        }
    )


def encode_arm_state(state: ArmState) -> bytes:
    """Message of an arm sample on ARM_STATE."""
    return _encode(
        {
            "joint_position_rad": [
                _finite_or_null(v) for v in state.joint_position_rad
            ],
            "joint_velocity_rad_s": [
                _finite_or_null(v) for v in state.joint_velocity_rad_s
            ],
        }
    )


def _finite_or_null(value: ParamValue) -> ParamValue:
    """None in place of NaN or infinity, which JSON cannot hold (RFC 8259)."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _encode(message: Mapping[str, object]) -> bytes:
    return json.dumps(message, allow_nan=False, separators=(",", ":")).encode()
