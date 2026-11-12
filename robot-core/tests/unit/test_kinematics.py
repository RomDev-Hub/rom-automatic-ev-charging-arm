"""Without Pinocchio, kinematics fails with a coded error instead of returning numbers."""

import sys

import pytest

from robot_core.arm import Kinematics, KinematicsUnavailableError, load_preset


def test_kinematics_without_pinocchio_raises_the_unavailable_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = load_preset("ur10e")
    # A None entry in sys.modules makes `import pinocchio` raise ImportError.
    monkeypatch.setitem(sys.modules, "pinocchio", None)
    with pytest.raises(KinematicsUnavailableError) as raised:
        Kinematics(model)
    assert raised.value.code == "arm.kinematics_unavailable"
