import type { channels, components } from "../../shared/contracts/asyncapi";
import { isRecord } from "../../shared/isRecord";

type Schemas = components["schemas"];
type PushMessage = channels["push"]["message"];
export type PushType = PushMessage["type"];
export type ChannelStatus = "connecting" | "open" | "closed";

/** A payload not yet checked: the field names of contract type `T`, each value still to be validated. */
export type Unchecked<T> = { readonly [K in keyof T]?: unknown };

/** A message of the push channel whose envelope matches the contract; consumers check the `data` they read. */
export interface PushEnvelope {
  type: PushType;
  data: Readonly<Record<string, unknown>>;
}

export const TELEMETRY_SNAPSHOT =
  "io.github.romdev-hub.ev-arm.telemetry.snapshot" satisfies Schemas["TelemetrySnapshot"]["type"];
export const PHASE_CHANGED =
  "io.github.romdev-hub.ev-arm.phase.changed" satisfies Schemas["PhaseChanged"]["type"];
export const COMMAND_LIFECYCLE =
  "io.github.romdev-hub.ev-arm.command.lifecycle" satisfies Schemas["CommandLifecycle"]["type"];

export interface PushHandlers {
  onStatus: (status: ChannelStatus) => void;
  onMessage: (envelope: PushEnvelope) => void;
}

export interface PushChannel {
  close: () => void;
}

const ADDRESS: channels["push"]["address"] = "/api/ws";
// REQ-HMI-004: a handshake is cancelled after 5 s; retries wait 1 s, doubling up to 15 s.
const HANDSHAKE_TIMEOUT_MS = 5_000;
const FIRST_RETRY_MS = 1_000;
const LAST_RETRY_MS = 15_000;

const PUSH_TYPES = {
  [TELEMETRY_SNAPSHOT]: true,
  [PHASE_CHANGED]: true,
  "io.github.romdev-hub.ev-arm.motion.blocked": true,
  "io.github.romdev-hub.ev-arm.fault.raised": true,
  "io.github.romdev-hub.ev-arm.supervision.changed": true,
  [COMMAND_LIFECYCLE]: true,
} satisfies Record<PushType, true>;

/** Skips a message that does not match contracts/asyncapi.yaml, without stopping the channel (REQ-HMI-006). */
export function ignoreMessage(message: unknown): void {
  console.warn(
    "push channel: ignored a message outside contracts/asyncapi.yaml",
    message,
  );
}

/** The single WSS connection of a signed-in HMI; a new connection opens only after the previous one has closed (REQ-HMI-004). */
export function openPushChannel(handlers: PushHandlers): PushChannel {
  let socket: WebSocket;
  let failures = 0;
  let handshakeTimer: ReturnType<typeof setTimeout> | undefined;
  let retryTimer: ReturnType<typeof setTimeout> | undefined;

  function connect() {
    handlers.onStatus("connecting");
    const current = new WebSocket(pushUrl());
    socket = current;
    handshakeTimer = setTimeout(() => {
      current.close();
    }, HANDSHAKE_TIMEOUT_MS);
    current.onopen = () => {
      clearTimeout(handshakeTimer);
      failures = 0;
      handlers.onStatus("open");
    };
    current.onmessage = (event: MessageEvent) => {
      const envelope = parseEnvelope(event.data);
      if (envelope) handlers.onMessage(envelope);
      else ignoreMessage(event.data);
    };
    current.onclose = () => {
      clearTimeout(handshakeTimer);
      handlers.onStatus("closed");
      retryTimer = setTimeout(
        connect,
        Math.min(FIRST_RETRY_MS * 2 ** failures, LAST_RETRY_MS),
      );
      failures += 1;
    };
  }

  connect();
  return {
    close() {
      clearTimeout(handshakeTimer);
      clearTimeout(retryTimer);
      socket.onopen = null;
      socket.onmessage = null;
      socket.onclose = null;
      socket.close();
    },
  };
}

function pushUrl(): string {
  const url = new URL(ADDRESS, window.location.href);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.href;
}

function parseEnvelope(raw: unknown): PushEnvelope | null {
  let message: unknown;
  try {
    message = typeof raw === "string" ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
  if (!isRecord(message) || !isRecord(message.data)) return null;
  const { type, data } = message;
  return typeof type === "string" && Object.hasOwn(PUSH_TYPES, type)
    ? { type: type as PushType, data }
    : null;
}
