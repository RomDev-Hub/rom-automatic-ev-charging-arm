"""Arm models described by URDF documents."""

from dataclasses import dataclass, field
from importlib.resources import files


@dataclass(frozen=True, slots=True)
class ArmModel:
    """An arm model: its name and its URDF document."""

    name: str
    urdf: str = field(repr=False)


def load_preset(name: str) -> ArmModel:
    """Load the preset model `robot_core/defaults/arms/<name>/model.urdf`, e.g. "ur10e"."""
    presets = files("robot_core").joinpath("defaults", "arms")
    if name not in {entry.name for entry in presets.iterdir() if entry.is_dir()}:
        raise ValueError(f"no preset arm model named {name!r}")
    urdf = presets.joinpath(name, "model.urdf").read_text(encoding="utf-8")
    return ArmModel(name=name, urdf=urdf)
