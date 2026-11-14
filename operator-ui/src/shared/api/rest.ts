import createClient from "openapi-fetch";
import type { components, paths } from "../contracts/openapi";
import { isRecord } from "../isRecord";

type Schemas = components["schemas"];
export type Credentials = Schemas["Credentials"];
export type SessionInfo = Schemas["SessionInfo"];
export type TelemetryData = Schemas["TelemetryData"];
export type CommandResult = Schemas["CommandResult"];

/** A message for the operator: a stable code and its parameters, put into words through the locale (REQ-I18N-004). */
export interface Notice {
  code: string;
  params: Readonly<Record<string, unknown>>;
}

export type Result<T> = { ok: true; data: T } | { ok: false; notice: Notice };

export const SESSION_REQUIRED = "err.auth.required";
export const NETWORK_ERROR = "hmi.error.network";
const HTTP_ERROR = "hmi.error.http";

const api = () => createClient<paths>({ baseUrl: window.location.origin });

export function openSession(
  credentials: Credentials,
): Promise<Result<SessionInfo>> {
  return settle(() => api().POST("/api/session", { body: credentials }));
}

export function readSession(): Promise<Result<SessionInfo>> {
  return settle(() => api().GET("/api/session"));
}

export function closeSession(): Promise<Result<unknown>> {
  return settle(() => api().DELETE("/api/session"));
}

export function readTelemetry(): Promise<Result<TelemetryData>> {
  return settle(() => api().GET("/api/telemetry"));
}

export function sendStop(): Promise<Result<CommandResult>> {
  return settle(() => api().POST("/api/commands/stop"));
}

async function settle<T>(
  send: () => Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<Result<T>> {
  let reply;
  try {
    reply = await send();
  } catch {
    return { ok: false, notice: { code: NETWORK_ERROR, params: {} } };
  }
  if (reply.response.ok) return { ok: true, data: reply.data as T };
  return {
    ok: false,
    notice: problemNotice(reply.error, reply.response.status),
  };
}

// Problem details carry the catalogue code (RFC 9457, ADR 0006); any other error body is named by its HTTP status.
function problemNotice(body: unknown, status: number): Notice {
  if (isRecord(body) && typeof body.code === "string") {
    return {
      code: body.code,
      params: isRecord(body.params) ? body.params : {},
    };
  }
  return { code: HTTP_ERROR, params: { status } };
}
