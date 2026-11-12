"""Kinematics and statics of an arm model, computed with Pinocchio.

Pinocchio is imported when a Kinematics is created, not when this module is imported:
the pin package is installed on Linux only (ADR 0008), and importing robot_core.arm
must work on every platform without side effects.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from robot_core.arm.model import ArmModel

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

type Vector3 = tuple[float, float, float]
type Matrix3 = tuple[Vector3, Vector3, Vector3]

BASE_FRAME = "base"
FLANGE_FRAME = "tool0"


class KinematicsUnavailableError(RuntimeError):
    """Pinocchio cannot be imported, so no kinematics can be computed."""

    code = "arm.kinematics_unavailable"


@dataclass(frozen=True, slots=True)
class Pose:
    """Pose of the flange frame `tool0` in the base frame `base`."""

    position: Vector3
    """Origin of `tool0`, in metres."""
    rotation: Matrix3
    """Rotation matrix, row by row, whose columns are the axes of `tool0`."""


class Kinematics:
    """Forward kinematics, Jacobian and gravity torque of one arm model.

    Results are in SI units and expressed in the URDF frame `base`, which coincides
    with the base frame of the UR controller; the URDF frame `base_link` is rotated by
    pi about z from it (ADR 0012). Joint positions are in radians, in chain order.
    The methods share one Pinocchio workspace, so an instance is not thread-safe.

    Raises KinematicsUnavailableError where Pinocchio cannot be imported.
    """

    def __init__(self, model: ArmModel) -> None:
        try:
            import pinocchio
        except ImportError as error:
            message = f"Pinocchio cannot be imported ({error}); kinematics unavailable"
            raise KinematicsUnavailableError(message) from error
        self._pinocchio = pinocchio
        self._model = pinocchio.buildModelFromXML(model.urdf)
        self._data = self._model.createData()
        self._base = self._model.getFrameId(BASE_FRAME)
        self._flange = self._model.getFrameId(FLANGE_FRAME)

    def forward_kinematics(self, joint_positions: Sequence[float]) -> Pose:
        """Pose of `tool0` at the given joint positions."""
        self._pinocchio.framesForwardKinematics(
            self._model, self._data, _configuration(joint_positions)
        )
        placement = self._data.oMf[self._base].actInv(self._data.oMf[self._flange])
        rotation = placement.rotation
        return Pose(
            position=_vector3(placement.translation),
            rotation=(
                _vector3(rotation[0]),
                _vector3(rotation[1]),
                _vector3(rotation[2]),
            ),
        )

    def jacobian(
        self, joint_positions: Sequence[float]
    ) -> tuple[tuple[float, ...], ...]:
        """Geometric Jacobian of `tool0` at the given joint positions.

        Rows 1 to 3 give the linear velocity of the origin of `tool0` and rows 4 to 6
        its angular velocity, both in the axes of `base`; one column per joint.
        """
        pinocchio = self._pinocchio
        pinocchio.computeJointJacobians(
            self._model, self._data, _configuration(joint_positions)
        )
        pinocchio.updateFramePlacements(self._model, self._data)
        world = pinocchio.getFrameJacobian(
            self._model, self._data, self._flange, pinocchio.LOCAL_WORLD_ALIGNED
        )
        to_base = self._data.oMf[self._base].rotation.T
        rows = (*(to_base @ world[:3]), *(to_base @ world[3:]))
        return tuple(tuple(float(value) for value in row) for row in rows)

    def gravity_torque(self, joint_positions: Sequence[float]) -> tuple[float, ...]:
        """Joint torques (N·m) that hold the arm still against gravity.

        Gravity is 9.81 m/s² along -z of `base`, i.e. the arm stands upright; the
        torques cover the links of the arm only, without a tool payload.
        """
        torque = self._pinocchio.computeGeneralizedGravity(
            self._model, self._data, _configuration(joint_positions)
        )
        return tuple(float(value) for value in torque)


def _configuration(joint_positions: Sequence[float]) -> NDArray[np.float64]:
    # Pinocchio accepts numpy arrays only; numpy is imported lazily like Pinocchio.
    import numpy

    return numpy.asarray(joint_positions, dtype=numpy.float64)


def _vector3(values: Any) -> Vector3:
    return (float(values[0]), float(values[1]), float(values[2]))
