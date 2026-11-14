import type { components } from "../../shared/contracts/asyncapi";
import type { Unchecked } from "../push/pushChannel";

type CommandState = components["schemas"]["CommandState"];

/** The states the HMI shows; "unknown" is set by the HMI when the connection is lost before the end (REQ-HMI-065). */
export type CommandStatus = CommandState | "unknown";

/** The latest command this HMI sent; `key` tells it apart before the core gives it a command_id. */
export interface CommandView {
  key: number;
  commandId: string | null;
  status: CommandStatus;
}

/** Commands correlated by command_id (REQ-HMI-007); events can arrive before the REST answer that names the command_id, so they wait in `unmatched`. */
export interface CommandLog {
  latest: CommandView | null;
  unmatched: ReadonlyMap<string, CommandState>;
}

export const EMPTY_LOG: CommandLog = { latest: null, unmatched: new Map() };

const UNMATCHED_LIMIT = 32;
const STATES = {
  pending: true,
  accepted: true,
  rejected: true,
  "timed-out": true,
  completed: true,
} satisfies Record<CommandState, true>;

function isFinal(status: CommandStatus): boolean {
  return status !== "pending" && status !== "accepted";
}

export function commandSent(log: CommandLog, key: number): CommandLog {
  return { ...log, latest: { key, commandId: null, status: "pending" } };
}

export function commandAnswered(
  log: CommandLog,
  key: number,
  commandId: string,
): CommandLog {
  const { latest } = log;
  if (latest?.key !== key) return log;
  const unmatched = new Map(log.unmatched);
  const status = unmatched.get(commandId) ?? latest.status;
  unmatched.delete(commandId);
  return { latest: { key, commandId, status }, unmatched };
}

/** The REST request failed: the core refused the command, or the outcome cannot be known. */
export function commandFailed(
  log: CommandLog,
  key: number,
  status: "rejected" | "unknown",
): CommandLog {
  const { latest } = log;
  if (latest?.key !== key || isFinal(latest.status)) return log;
  return { ...log, latest: { ...latest, status } };
}

/** The log after a commandLifecycle event; null when the event breaks the contract. */
export function lifecycleReceived(
  log: CommandLog,
  data: Unchecked<components["schemas"]["CommandLifecycleData"]>,
): CommandLog | null {
  const { command_id: commandId, state } = data;
  if (typeof commandId !== "string" || !isCommandState(state)) return null;
  const { latest } = log;
  if (latest?.commandId === commandId) {
    return isFinal(latest.status)
      ? log
      : { ...log, latest: { ...latest, status: state } };
  }
  const unmatched = new Map(log.unmatched);
  const known = unmatched.get(commandId);
  if (known === undefined || !isFinal(known)) unmatched.set(commandId, state);
  for (const oldest of unmatched.keys()) {
    if (unmatched.size <= UNMATCHED_LIMIT) break;
    unmatched.delete(oldest);
  }
  return { ...log, unmatched };
}

export function channelLost(log: CommandLog): CommandLog {
  const { latest } = log;
  if (latest === null || isFinal(latest.status)) return log;
  return { ...log, latest: { ...latest, status: "unknown" } };
}

function isCommandState(value: unknown): value is CommandState {
  return typeof value === "string" && Object.hasOwn(STATES, value);
}
