import { vi } from "vitest";

const CLOSING = 2;
const CLOSED = 3;

/** Test double of the browser WebSocket: a test opens, feeds and drops each connection the code creates. */
export class FakeWebSocket {
  static readonly instances: FakeWebSocket[] = [];
  readonly url: string;
  readyState = 0;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: unknown }) => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  // Like a browser, the close event arrives after close() returns.
  close(): void {
    if (this.readyState >= CLOSING) return;
    this.readyState = CLOSING;
    queueMicrotask(() => {
      this.readyState = CLOSED;
      this.onclose?.();
    });
  }

  open(): void {
    this.readyState = 1;
    this.onopen?.();
  }

  receive(message: unknown): void {
    const data =
      typeof message === "string" ? message : JSON.stringify(message);
    this.onmessage?.({ data });
  }

  drop(): void {
    this.readyState = CLOSED;
    this.onclose?.();
  }
}

/** Replaces the global WebSocket for one test; returns the connections created, oldest first. */
export function installFakeWebSocket(): FakeWebSocket[] {
  FakeWebSocket.instances.length = 0;
  vi.stubGlobal("WebSocket", FakeWebSocket);
  return FakeWebSocket.instances;
}
