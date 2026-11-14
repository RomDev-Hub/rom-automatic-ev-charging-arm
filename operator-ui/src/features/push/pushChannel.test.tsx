import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { installFakeWebSocket, type FakeWebSocket } from "./fakeWebSocket";
import {
  openPushChannel,
  type ChannelStatus,
  type PushEnvelope,
} from "./pushChannel";

const TELEMETRY = "io.github.romdev-hub.ev-arm.telemetry.snapshot";

let sockets: FakeWebSocket[];
let statuses: ChannelStatus[];
let messages: PushEnvelope[];

function open() {
  return openPushChannel({
    onStatus: (status) => statuses.push(status),
    onMessage: (envelope) => messages.push(envelope),
  });
}

function latest(): FakeWebSocket {
  const socket = sockets.at(-1);
  if (socket === undefined) throw new Error("no connection was opened");
  return socket;
}

beforeEach(() => {
  vi.useFakeTimers();
  sockets = installFakeWebSocket();
  statuses = [];
  messages = [];
});

afterEach(() => {
  vi.useRealTimers();
});

describe("openPushChannel", () => {
  it("connects to /api/ws on the origin of the page", () => {
    open();

    expect(sockets.map((socket) => socket.url)).toEqual([
      "ws://localhost:3000/api/ws",
    ]);
  });

  it("retries after 1, 2, 4, 8, 15 and 15 s, and after 1 s again once connected", () => {
    open();
    const waits: number[] = [];

    for (let attempt = 0; attempt < 6; attempt += 1) {
      const before = sockets.length;
      latest().drop();
      let waited = 0;
      while (sockets.length === before) {
        vi.advanceTimersByTime(500);
        waited += 500;
      }
      waits.push(waited);
    }
    latest().open();
    latest().drop();
    vi.advanceTimersByTime(1_000);

    expect(waits).toEqual([1_000, 2_000, 4_000, 8_000, 15_000, 15_000]);
    expect(sockets).toHaveLength(8);
  });

  it("cancels a handshake longer than 5 s and retries only after that connection closed", async () => {
    open();

    vi.advanceTimersByTime(5_000);
    expect(latest().readyState).toBe(2);
    expect(sockets).toHaveLength(1);
    await vi.advanceTimersByTimeAsync(1_000);

    expect(sockets).toHaveLength(2);
    expect(statuses).toEqual(["connecting", "closed", "connecting"]);
  });

  it("stops for good when closed", async () => {
    const channel = open();
    latest().open();

    channel.close();
    await vi.advanceTimersByTimeAsync(60_000);

    expect(sockets).toHaveLength(1);
    expect(latest().readyState).toBe(3);
    expect(statuses).toEqual(["connecting", "open"]);
  });

  it("skips a message outside the contract with a warning and keeps delivering", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    open();
    latest().open();

    latest().receive("{not json");
    latest().receive({ type: "io.github.romdev-hub.ev-arm.unknown", data: {} });
    latest().receive({ type: TELEMETRY, data: { data_origin: "simulated" } });

    expect(warn).toHaveBeenCalledTimes(2);
    expect(messages).toEqual([
      { type: TELEMETRY, data: { data_origin: "simulated" } },
    ]);
  });
});
