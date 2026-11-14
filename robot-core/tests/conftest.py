"""Fixtures shared by the robot-core test suite."""

import pytest


class VirtualClock:
    """Monotonic clock that moves only when a test advances it."""

    def __init__(self, start_s: float) -> None:
        self.now_s = start_s

    def __call__(self) -> float:
        return self.now_s

    def advance(self, seconds: float) -> None:
        self.now_s += seconds


@pytest.fixture
def clock() -> VirtualClock:
    # Far from zero, so code that mistakes a time stamp for a duration shows up.
    return VirtualClock(start_s=1000.0)
