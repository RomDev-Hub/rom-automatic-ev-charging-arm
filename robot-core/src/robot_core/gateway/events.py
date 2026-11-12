"""Messages of the push channel: CloudEvents 1.0 envelopes, numbered and fanned out.

Envelope and types follow contracts/asyncapi.yaml.
"""

import asyncio
import json
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime

from robot_core.mission.machine import Transition

SPEC_VERSION = "1.0"
TYPE_PREFIX = "io.github.romdev-hub.ev-arm."
PHASE_CHANGED = TYPE_PREFIX + "phase.changed"
SUBSCRIPTION_CAPACITY = 64


class Subscription:
    """Messages waiting for one connection; None ends them once it fell behind."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[str | None] = asyncio.Queue(SUBSCRIPTION_CAPACITY)

    async def next(self) -> str | None:
        return await self._queue.get()

    def offer(self, message: str) -> bool:
        """Queue a message; when the queue is full, end it instead and say False."""
        try:
            self._queue.put_nowait(message)
        except asyncio.QueueFull:
            while not self._queue.empty():
                self._queue.get_nowait()
            self._queue.put_nowait(None)
            return False
        return True


class EventHub:
    """Numbers each message of the run and offers it to every connection.

    Publishing never waits: a connection whose queue is full is dropped, so a slow
    client holds up neither the others nor the supervision loop (REQ-GW-018).
    """

    def __init__(self, run_id: str) -> None:
        self.source = f"/core/{run_id}"
        self._sequence = 0
        self._subscriptions: set[Subscription] = set()

    def subscribe(self) -> Subscription:
        subscription = Subscription()
        self._subscriptions.add(subscription)
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        self._subscriptions.discard(subscription)

    def publish_phase(self, transition: Transition) -> None:
        """Announce a phase change as it happens (REQ-GW-008)."""
        self._publish(
            PHASE_CHANGED,
            {
                "previous": transition.previous,
                "phase": transition.phase,
                "code": transition.code,
                "params": dict(transition.params),
                "expected_next": transition.expected_next,
            },
        )

    def _publish(self, event_type: str, data: Mapping[str, object]) -> None:
        self._sequence += 1
        now = datetime.now(UTC).isoformat(timespec="milliseconds")
        envelope = {
            "specversion": SPEC_VERSION,
            "id": str(uuid.uuid7()),
            "source": self.source,
            "type": event_type,
            "time": now.replace("+00:00", "Z"),
            # Fixed width, so string order is numeric order (CloudEvents sequence).
            "sequence": f"{self._sequence:020d}",
            "data": data,
        }
        message = json.dumps(envelope, ensure_ascii=False, allow_nan=False)
        for subscription in list(self._subscriptions):
            if not subscription.offer(message):
                self._subscriptions.discard(subscription)
