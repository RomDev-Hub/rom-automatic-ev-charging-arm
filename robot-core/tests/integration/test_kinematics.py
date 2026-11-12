"""Pinocchio on the UR10e preset agrees with the kinematics and masses UR publishes."""

import numpy as np
import pytest

from robot_core.arm import Kinematics, load_preset

pytest.importorskip("pinocchio")

# UR10e table of https://www.universal-robots.com/articles/ur/application-installation/dh-parameters-for-calculations-of-kinematics-and-dynamics/
# in the standard DH convention; the centre of mass of link i is given in DH frame i.
DH_A = (0.0, -0.6127, -0.57155, 0.0, 0.0, 0.0)
DH_D = (0.1807, 0.0, 0.0, 0.17415, 0.11985, 0.11655)
DH_ALPHA = (np.pi / 2, 0.0, 0.0, np.pi / 2, -np.pi / 2, 0.0)
LINK_MASS = (7.369, 13.051, 3.989, 2.1, 1.98, 0.615)
LINK_CENTRE_OF_MASS = (
    (0.021, 0.0, 0.027),
    (0.38, 0.0, 0.158),
    (0.24, 0.0, 0.068),
    (0.0, 0.007, 0.018),
    (0.0, 0.007, 0.018),
    (0.0, 0.0, -0.026),
)
GRAVITY = 9.81

CONFIGURATIONS = np.random.default_rng(2026).uniform(-np.pi, np.pi, size=(1000, 6))
TOLERANCE = 1e-6  # REQ-ARM-023
FINITE_DIFFERENCE_STEP = 1e-6


@pytest.fixture(scope="module")
def kinematics() -> Kinematics:
    return Kinematics(load_preset("ur10e"))


def dh_frames(q: np.ndarray) -> list[np.ndarray]:
    """Homogeneous transforms of DH frames 0 to 6 in frame 0."""
    frames = [np.eye(4)]
    for theta, d, a, alpha in zip(q, DH_D, DH_A, DH_ALPHA, strict=True):
        ct, st, ca, sa = np.cos(theta), np.sin(theta), np.cos(alpha), np.sin(alpha)
        link = np.array(
            [
                [ct, -st * ca, st * sa, a * ct],
                [st, ct * ca, -ct * sa, a * st],
                [0.0, sa, ca, d],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        frames.append(frames[-1] @ link)
    return frames


def skew_vector(matrix: np.ndarray) -> np.ndarray:
    """Vector of M - M^T; for a rotation, its axis times twice the sine of its angle."""
    return np.array(
        [
            matrix[2, 1] - matrix[1, 2],
            matrix[0, 2] - matrix[2, 0],
            matrix[1, 0] - matrix[0, 1],
        ]
    )


def rotation_angle(rotation: np.ndarray) -> float:
    """Angle of a rotation matrix, accurate near 0 and near pi."""
    sine = np.linalg.norm(skew_vector(rotation)) / 2
    cosine = (np.trace(rotation) - 1) / 2
    return float(np.arctan2(sine, cosine))


def finite_difference_jacobian(kinematics: Kinematics, q: np.ndarray) -> np.ndarray:
    """Central differences of the pose of tool0: linear then angular velocity."""
    columns = []
    for joint in range(len(q)):
        step = np.zeros(len(q))
        step[joint] = FINITE_DIFFERENCE_STEP
        after = kinematics.forward_kinematics(q + step)
        before = kinematics.forward_kinematics(q - step)
        linear = (np.array(after.position) - np.array(before.position)) / (
            2 * FINITE_DIFFERENCE_STEP
        )
        turn = np.array(after.rotation) @ np.array(before.rotation).T
        angular = skew_vector(turn) / (4 * FINITE_DIFFERENCE_STEP)
        columns.append(np.concatenate((linear, angular)))
    return np.column_stack(columns)


def static_gravity_torque(q: np.ndarray) -> np.ndarray:
    """Torque each joint needs to hold the links still, from the published masses."""
    frames = dh_frames(q)
    torque = np.zeros(len(q))
    for link, (mass, centre) in enumerate(
        zip(LINK_MASS, LINK_CENTRE_OF_MASS, strict=True), start=1
    ):
        centre_in_base = (frames[link] @ np.append(centre, 1.0))[:3]
        weight = np.array([0.0, 0.0, -mass * GRAVITY])
        # Joints 1 to `link` carry this link; joint k turns about z of DH frame k - 1.
        for joint, frame in enumerate(frames[:link]):
            axis, origin = frame[:3, 2], frame[:3, 3]
            torque[joint] -= np.cross(centre_in_base - origin, weight) @ axis
    return torque


def test_fk_of_tool0_in_base_matches_the_dh_table(kinematics: Kinematics) -> None:
    position_errors, rotation_errors = [], []
    for q in CONFIGURATIONS:
        pose = kinematics.forward_kinematics(q)
        expected = dh_frames(q)[-1]
        position_errors.append(
            np.linalg.norm(np.array(pose.position) - expected[:3, 3])
        )
        rotation_errors.append(
            rotation_angle(expected[:3, :3].T @ np.array(pose.rotation))
        )
    assert max(position_errors) <= TOLERANCE
    assert max(rotation_errors) <= TOLERANCE


def test_jacobian_matches_finite_differences_of_fk(kinematics: Kinematics) -> None:
    errors = [
        np.max(
            np.abs(
                np.array(kinematics.jacobian(q))
                - finite_difference_jacobian(kinematics, q)
            )
        )
        for q in CONFIGURATIONS
    ]
    assert max(errors) <= TOLERANCE


def test_gravity_torque_matches_the_published_masses_and_centres_of_mass(
    kinematics: Kinematics,
) -> None:
    errors = [
        np.max(
            np.abs(np.array(kinematics.gravity_torque(q)) - static_gravity_torque(q))
        )
        for q in CONFIGURATIONS
    ]
    assert max(errors) <= TOLERANCE
