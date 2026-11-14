"""The push channel /api/ws: one WSS connection per client carries every message."""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from robot_core.gateway.events import EventHub, Subscription
from robot_core.gateway.problems import ProblemCode, problem_response
from robot_core.gateway.sessions import COOKIE_NAME, SessionStore

SEND_TIMEOUT_S = 0.25  # REQ-GW-018
POLICY_VIOLATION = 1008  # close code of RFC 6455


def push_routes(events: EventHub, sessions: SessionStore) -> APIRouter:
    router = APIRouter()

    @router.websocket("/api/ws")
    async def push_channel(websocket: WebSocket) -> None:
        """Push every message of the channel to a client with a valid session.

        Without one, the handshake is refused before the upgrade (REQ-AUTH-006); the
        session comes from the cookie only, never from the URL (REQ-AUTH-005). The
        channel takes no message: a client that sends one is disconnected
        (REQ-GW-006).
        """
        if sessions.find(websocket.cookies.get(COOKIE_NAME)) is None:
            denial = problem_response(ProblemCode.AUTH_REQUIRED)
            await websocket.send_denial_response(denial)
            return
        subscription = events.subscribe()
        try:
            await websocket.accept()
            close_code = await _serve(websocket, subscription)
            if close_code is not None:
                await websocket.close(close_code)
        finally:
            events.unsubscribe(subscription)

    return router


async def _serve(websocket: WebSocket, subscription: Subscription) -> int | None:
    """Forward messages until either side ends; the close code to send, if any."""
    forward = asyncio.create_task(_forward(websocket, subscription))
    refuse = asyncio.create_task(_refuse_input(websocket))
    try:
        done, _ = await asyncio.wait(
            {forward, refuse}, return_when=asyncio.FIRST_COMPLETED
        )
    finally:
        forward.cancel()
        refuse.cancel()
        # Not gather: a cancelled gather raises a child's CancelledError in this
        # task, which the server's own cancel scope then cannot recognise.
        await asyncio.wait({forward, refuse})
    return done.pop().result()


async def _forward(websocket: WebSocket, subscription: Subscription) -> int | None:
    while (message := await subscription.next()) is not None:
        try:
            await asyncio.wait_for(websocket.send_text(message), SEND_TIMEOUT_S)
        except TimeoutError:
            return POLICY_VIOLATION
        except WebSocketDisconnect:
            return None
    return POLICY_VIOLATION  # fell behind, and the hub dropped the subscription


async def _refuse_input(websocket: WebSocket) -> int | None:
    message = await websocket.receive()
    return None if message["type"] == "websocket.disconnect" else POLICY_VIOLATION
