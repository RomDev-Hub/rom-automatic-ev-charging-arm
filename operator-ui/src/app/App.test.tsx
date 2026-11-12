import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../shared/i18n/I18nProvider";
import { App } from "./App";
import { createOperatorStore } from "./operatorStore";

const ADMIN = { username: "admin", roles: ["admin"] };

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

  it("signs out through the session route", async () => {
    const requests = serve({
      "GET /api/session": () => json(200, ADMIN),
      "DELETE /api/session": () => new Response(null, { status: 204 }),
    });
    await renderApp();

    fireEvent.click(screen.getByRole("button", { name: "Đăng xuất" }));

    expect(
      await screen.findByRole("button", { name: "Đăng nhập" }),
    ).toBeInstanceOf(HTMLButtonElement);
    expect(requests.map(route)).toEqual([
      "GET /api/session",
      "DELETE /api/session",
    ]);
  });
});
