import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  installFakeWebSocket,
  type FakeWebSocket,
} from "../features/push/fakeWebSocket";
import { I18nProvider } from "../shared/i18n/I18nProvider";
import { App } from "./App";
import { createOperatorStore } from "./operatorStore";

const ADMIN = { username: "admin", roles: ["admin"] };

let sockets: FakeWebSocket[];

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function problem(status: number, code: string): Response {
  const body = {
    type: `tag:test/${code}`,
    status,
    title: code,
    code,
    params: {},
  };
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/problem+json" },
  });
}

function route(request: Request): string {
  return `${request.method} ${new URL(request.url).pathname}`;
}

/** Answers each request from `routes`, keyed "METHOD /path", and records every request. */
function serve(routes: Record<string, () => Response>): Request[] {
  const requests: Request[] = [];
  vi.stubGlobal("fetch", (request: Request) => {
    requests.push(request);
    const reply = routes[route(request)];
    return reply
      ? Promise.resolve(reply())
      : Promise.reject(new TypeError(`no route for ${route(request)}`));
  });
  return requests;
}

async function renderApp() {
  const store = createOperatorStore();
  render(
    <I18nProvider>
      <App store={store} />
    </I18nProvider>,
  );
  await act(() => store.checkSession());
  return store;
}

function signIn(username: string, password: string) {
  fireEvent.change(screen.getByLabelText("Tên đăng nhập"), {
    target: { value: username },
  });
  fireEvent.change(screen.getByLabelText("Mật khẩu"), {
    target: { value: password },
  });
  fireEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));
}

beforeEach(() => {
  sockets = installFakeWebSocket();
});

afterEach(() => {
  localStorage.clear();
});

describe("session", () => {
  it("shows only the login form and sends nothing but the session check before sign-in", async () => {
    const requests = serve({
      "GET /api/session": () => problem(401, "err.auth.required"),
    });

    await renderApp();

    expect(screen.getByRole("button", { name: "Đăng nhập" })).toBeInstanceOf(
      HTMLButtonElement,
    );
    expect(screen.queryByRole("button", { name: "Đăng xuất" })).toBeNull();
    expect(requests.map(route)).toEqual(["GET /api/session"]);
    expect(sockets).toHaveLength(0);
  });

  it("signs in with the credentials in the request body only", async () => {
    const requests = serve({
      "GET /api/session": () => problem(401, "err.auth.required"),
      "POST /api/session": () => json(200, ADMIN),
    });
    await renderApp();

    signIn("admin", "correct horse");

    expect(
      await screen.findByRole("button", { name: "Đăng xuất" }),
    ).toBeInstanceOf(HTMLButtonElement);
    const [, login] = requests;
    expect(login && route(login)).toBe("POST /api/session");
    expect(login && new URL(login.url).search).toBe("");
    expect(await login?.json()).toEqual({
      username: "admin",
      password: "correct horse",
    });
    expect([localStorage.length, sessionStorage.length]).toEqual([0, 0]);
    expect(sockets.map((socket) => socket.url)).toEqual([
      "ws://localhost:3000/api/ws",
    ]);
  });

  it("tells why sign-in was refused, from the problem code", async () => {
    serve({
      "GET /api/session": () => problem(401, "err.auth.required"),
      "POST /api/session": () => problem(401, "err.auth.invalid_credentials"),
    });
    await renderApp();

    signIn("admin", "wrong");

    expect((await screen.findByRole("alert")).textContent).toBe(
      "Tên đăng nhập hoặc mật khẩu không đúng",
    );
  });

  it("signs out through the session route and closes the push connection", async () => {
    const requests = serve({
      "GET /api/session": () => json(200, ADMIN),
      "DELETE /api/session": () => new Response(null, { status: 204 }),
    });
    await renderApp();
    act(() => sockets[0]?.open());

    fireEvent.click(screen.getByRole("button", { name: "Đăng xuất" }));

    expect(
      await screen.findByRole("button", { name: "Đăng nhập" }),
    ).toBeInstanceOf(HTMLButtonElement);
    expect(requests.map(route)).toEqual([
      "GET /api/session",
      "DELETE /api/session",
    ]);
    expect(sockets.map((socket) => socket.readyState)).toEqual([3]);
  });

  it("returns to the login form when a dropped connection finds the session refused", async () => {
    const routes = { "GET /api/session": () => json(200, ADMIN) };
    serve(routes);
    await renderApp();
    routes["GET /api/session"] = () => problem(401, "err.auth.required");

    act(() => sockets[0]?.drop());

    expect((await screen.findByRole("alert")).textContent).toBe(
      "Chưa đăng nhập hoặc phiên đăng nhập đã hết hạn",
    );
    expect(sockets).toHaveLength(1);
  });
});
