"""End-to-end smoke test of the simulation stack, through the hmi service.

Builds and starts deploy/compose.yaml plus deploy/compose.sim.yaml, waits until core
and hmi are healthy and creates an admin account with `docker compose run`. With
--no-build it skips the build and starts the images already tagged ev-arm-core:sim and
ev-arm-hmi:sim, as the CI job does after building them with its own cache. Then it
checks through https://127.0.0.1:8443, with TLS verification off because Caddy signs
with its internal CA: the page and its CSP, login, the session, telemetry, one
telemetry message on the WSS channel, and the Stop lifecycle ending in SAFE_STOP.
The stack and its volumes are removed at the end, also after a failure.

Standard library only, so the same file runs on a CI runner and on a developer
machine, Linux or Windows. Prints one line per check; exits 0 when every check
passes, 1 otherwise.
"""

import argparse
import base64
import hashlib
import http.client
import json
import os
import queue
import secrets
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

REPOSITORY = Path(__file__).resolve().parents[1]
COMPOSE = [
    "docker",
    "compose",
    "-f",
    str(REPOSITORY / "deploy" / "compose.yaml"),
    "-f",
    str(REPOSITORY / "deploy" / "compose.sim.yaml"),
]
HOST = "127.0.0.1"
PORT = 8443
TIMEOUT_S = 10.0
HEALTHY_TIMEOUT_S = 180
# Message types of the push channel, from contracts/asyncapi.yaml.
TELEMETRY = "io.github.romdev-hub.ev-arm.telemetry.snapshot"
PHASE_CHANGED = "io.github.romdev-hub.ev-arm.phase.changed"
COMMAND_LIFECYCLE = "io.github.romdev-hub.ev-arm.command.lifecycle"
# RFC 6455, section 1.3.
WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

TLS = ssl.create_default_context()
TLS.check_hostname = False
TLS.verify_mode = ssl.CERT_NONE

Message = dict[str, Any]


class CheckFailed(Exception):
    """A check that did not hold; the message says what was seen instead."""


def expect(condition: bool, seen: str) -> None:
    if not condition:
        raise CheckFailed(seen)


def compose(*args: str, stdin: str | None = None, progress: bool = False) -> str:
    """Run `docker compose` on the simulation stack and return its standard output.

    With `progress`, all output goes to stderr as it comes, for long builds.
    """
    result = subprocess.run(
        [*COMPOSE, *args],
        input=stdin,
        stdout=sys.stderr if progress else subprocess.PIPE,
        stderr=sys.stderr if progress else subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        lines = f"{result.stdout or ''}\n{result.stderr or ''}".strip().splitlines()
        last = lines[-1] if lines else "see the output above"
        raise CheckFailed(
            f"docker compose {args[0]} exited {result.returncode}: {last}"
        )
    return result.stdout or ""


def https(
    method: str, path: str, *, body: object = None, cookie: str | None = None
) -> tuple[int, http.client.HTTPMessage, bytes]:
    connection = http.client.HTTPSConnection(HOST, PORT, timeout=TIMEOUT_S, context=TLS)
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if cookie is not None:
        headers["Cookie"] = cookie
    payload = json.dumps(body).encode() if body is not None else None
    try:
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        return response.status, response.headers, response.read()
    finally:
        connection.close()


def https_json(method: str, path: str, *, cookie: str, body: object = None) -> Message:
    """The JSON body of a request that must answer 200."""
    status, _, raw = https(method, path, body=body, cookie=cookie)
    expect(status == 200, f"{method} {path} answered HTTP {status}: {raw[:200]!r}")
    data: Message = json.loads(raw)
    return data


class PushChannel:
    """Minimal RFC 6455 client of /api/ws; a thread reads every message as it comes.

    The server drops a client that falls behind, so messages are read continuously
    and queued here. The client never writes after the handshake.
    """

    def __init__(self, cookie: str) -> None:
        # No server name, hence no SNI: Caddy then answers with its 127.0.0.1 site.
        connection = socket.create_connection((HOST, PORT), TIMEOUT_S)
        self._socket = TLS.wrap_socket(connection)
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            "GET /api/ws HTTP/1.1\r\n"
            f"Host: {HOST}:{PORT}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            f"Origin: https://{HOST}:{PORT}\r\n"
            f"Cookie: {cookie}\r\n\r\n"
        )
        self._socket.sendall(handshake.encode())
        self._reader = self._socket.makefile("rb")
        status = self._reader.readline().decode("latin-1").strip()
        headers = {}
        while line := self._reader.readline().decode("latin-1").strip():
            name, _, value = line.partition(":")
            headers[name.strip().lower()] = value.strip()
        digest = hashlib.sha1((key + WEBSOCKET_GUID).encode(), usedforsecurity=False)
        accept = base64.b64encode(digest.digest()).decode()
        if (
            not status.startswith("HTTP/1.1 101")
            or headers.get("sec-websocket-accept") != accept
        ):
            self.close()
            raise CheckFailed(f"handshake answered {status!r}")
        self._socket.settimeout(None)
        self._messages: queue.Queue[Message | None] = queue.Queue()
        threading.Thread(target=self._read_messages, daemon=True).start()

    def next(self, wanted: Callable[[Message], bool]) -> Message:
        """The next message for which `wanted` holds, skipping the others."""
        deadline = time.monotonic() + TIMEOUT_S
        while (remaining := deadline - time.monotonic()) > 0:
            try:
                message = self._messages.get(timeout=remaining)
            except queue.Empty:
                break
            if message is None:
                raise CheckFailed("the push channel closed")
            if wanted(message):
                return message
        raise CheckFailed(f"no such message within {TIMEOUT_S:.0f} s")

    def close(self) -> None:
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self._socket.close()

    def _read_messages(self) -> None:
        text = b""
        try:
            while True:
                final, opcode, payload = self._read_frame()
                if opcode == 0x8:  # close
                    break
                if opcode in (0x0, 0x1):  # continuation, text
                    text += payload
                    if final:
                        self._messages.put(json.loads(text))
                        text = b""
        except (OSError, EOFError, ValueError):
            pass
        finally:
            self._messages.put(None)

    def _read_frame(self) -> tuple[bool, int, bytes]:
        first, second = self._read_exact(2)
        length = second & 0x7F
        if length == 126:
            (length,) = struct.unpack("!H", self._read_exact(2))
        elif length == 127:
            (length,) = struct.unpack("!Q", self._read_exact(8))
        mask = self._read_exact(4) if second & 0x80 else b""
        payload = self._read_exact(length)
        if mask:
            payload = bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))
        return bool(first & 0x80), first & 0x0F, payload

    def _read_exact(self, size: int) -> bytes:
        data = self._reader.read(size)
        if len(data) < size:
            raise EOFError("the push channel closed")
        return data


class Run:
    """The checks, in order; each returns what it saw, or raises CheckFailed."""

    def __init__(self, build: bool) -> None:
        self.build = build
        self.username = f"e2e-{secrets.token_hex(4)}"
        self.password = secrets.token_urlsafe(18)
        self.cookie = ""
        self.channel: PushChannel | None = None

    def stack_healthy(self) -> str:
        start = time.monotonic()
        # Without a build, a missing image is an error rather than a pull from a registry.
        images = ("--build",) if self.build else ("--no-build", "--pull", "never")
        wait = ("--wait", "--wait-timeout", str(HEALTHY_TIMEOUT_S))
        compose("up", *images, "--detach", *wait, progress=True)
        elapsed_s = time.monotonic() - start
        source = "build included" if self.build else "images built beforehand"
        return f"core and hmi healthy after {elapsed_s:.0f} s, {source}"

    def admin_created(self) -> str:
        # The password goes on stdin, never on the command line.
        command = ("run", "--rm", "-T", "core", "robot-core", "admin", "create")
        compose(*command, self.username, stdin=self.password + "\n")
        return f"account {self.username} created by docker compose run"

    def page_and_csp(self) -> str:
        status, headers, body = https("GET", "/")
        expect(status == 200, f"GET / answered HTTP {status}")
        content_type = headers.get("Content-Type", "")
        expect(content_type.startswith("text/html"), f"Content-Type {content_type!r}")
        expect(b"<!doctype html" in body[:200].lower(), "the page is not HTML")
        policy = headers.get("Content-Security-Policy", "")
        expect("default-src 'self'" in policy, f"Content-Security-Policy {policy!r}")
        return f"GET / 200 text/html, Content-Security-Policy: {policy}"

    def login(self) -> str:
        credentials = {"username": self.username, "password": self.password}
        status, headers, body = https("POST", "/api/session", body=credentials)
        expect(status == 200, f"POST /api/session answered HTTP {status}: {body!r}")
        cookies = [
            cookie
            for cookie in headers.get_all("Set-Cookie", [])
            if cookie.startswith("__Host-")
        ]
        expect(len(cookies) == 1, f"{len(cookies)} session cookies")
        pair, *attributes = (part.strip() for part in cookies[0].split(";"))
        flags = {attribute.lower() for attribute in attributes}
        expect(
            {"secure", "httponly", "samesite=strict"} <= flags,
            f"cookie attributes {sorted(flags)}",
        )
        self.cookie = pair
        name = pair.split("=", 1)[0]
        return f"POST /api/session 200, cookie {name}: {'; '.join(attributes)}"

    def session(self) -> str:
        data = https_json("GET", "/api/session", cookie=self.cookie)
        expect(data.get("username") == self.username, f"session {data}")
        expect("admin" in data.get("roles", []), f"roles {data.get('roles')}")
        return f"GET /api/session 200, {data['username']} with roles {data['roles']}"

    def telemetry(self) -> str:
        data = https_json("GET", "/api/telemetry", cookie=self.cookie)
        return f"GET /api/telemetry 200, phase {data['phase']['phase']}"

    def push_telemetry(self) -> str:
        self.channel = PushChannel(self.cookie)
        message = self.channel.next(lambda m: m["type"] == TELEMETRY)
        phase = message["data"]["phase"]["phase"]
        sequence = int(message["sequence"])
        return f"WSS /api/ws 101, telemetry message {sequence}, phase {phase}"

    def stop_lifecycle(self) -> str:
        assert self.channel is not None, "the push channel opens in an earlier check"
        result = https_json("POST", "/api/commands/stop", cookie=self.cookie)
        expect(result.get("code") == "cmd.stop.engaged", f"Stop answered {result}")
        command_id = result["command_id"]

        def of_stop(message: Message) -> bool:
            if message["type"] == PHASE_CHANGED:
                return True
            return (
                message["type"] == COMMAND_LIFECYCLE
                and message["data"]["command_id"] == command_id
            )

        steps: list[str] = []
        while not steps or steps[-1] != "completed":
            data = self.channel.next(of_stop)["data"]
            steps.append(data.get("state") or f"phase {data['phase']}")
        expect(
            steps == ["pending", "accepted", "phase SAFE_STOP", "completed"],
            f"lifecycle {steps}",
        )
        expect(data.get("code") == "cmd.stop.engaged", f"completed with {data}")
        after = self.channel.next(lambda m: m["type"] == TELEMETRY)
        phase = after["data"]["phase"]["phase"]
        expect(phase == "SAFE_STOP", f"telemetry after Stop in phase {phase}")
        return f"Stop {' -> '.join(steps)}; telemetry then in phase {phase}"


def report(status: str, name: str, detail: str) -> None:
    print(f"{status} {name}: {' '.join(detail.split())}", flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="start the stack from the images already tagged ev-arm-core:sim and ev-arm-hmi:sim instead of building them",
    )
    options = parser.parse_args(argv)
    try:
        existing = compose("ps", "--all", "--quiet").split()
    except (CheckFailed, OSError) as error:
        report("FAIL", "preflight", f"docker compose is not usable: {error}")
        return 1
    if existing:
        # Never replace or delete a stack someone else started under the same name.
        report("FAIL", "preflight", "project ev-arm has containers; stop it first")
        return 1

    run = Run(build=not options.no_build)
    checks = [
        ("stack healthy", run.stack_healthy),
        ("admin account", run.admin_created),
        ("page and CSP", run.page_and_csp),
        ("login", run.login),
        ("session", run.session),
        ("telemetry", run.telemetry),
        ("push channel", run.push_telemetry),
        ("Stop lifecycle", run.stop_lifecycle),
    ]
    passed = True
    try:
        for name, check in checks:
            if not passed:
                report("SKIP", name, "an earlier check failed")
                continue
            try:
                report("PASS", name, check())
            except (CheckFailed, OSError, KeyError, TypeError, ValueError) as error:
                report("FAIL", name, f"{type(error).__name__}: {error}")
                passed = False
    finally:
        if run.channel is not None:
            run.channel.close()
        try:
            compose("down", "--volumes", "--remove-orphans")
            report("PASS", "teardown", "containers, volumes and networks removed")
        except (CheckFailed, OSError) as error:
            report("FAIL", "teardown", str(error))
            passed = False
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
