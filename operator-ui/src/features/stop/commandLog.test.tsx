import { describe, expect, it } from "vitest";
import {
  channelLost,
  commandAnswered,
  commandSent,
  EMPTY_LOG,
  lifecycleReceived,
  type CommandLog,
} from "./commandLog";

const ID = "0193a1f2-7d20-7c41-8e10-5b9f2a3c4d5e";

function received(log: CommandLog, state: string): CommandLog {
  const next = lifecycleReceived(log, {
    command_id: ID,
    command: "stop",
    state,
  });
  if (next === null) throw new Error(`event refused: ${state}`);
  return next;
}

describe("command log", () => {
  it("matches lifecycle events that arrived before the REST answer", () => {
    let log = commandSent(EMPTY_LOG, 1);
    log = received(log, "pending");
    log = received(log, "accepted");
    log = received(log, "completed");

    log = commandAnswered(log, 1, ID);

    expect(log.latest).toEqual({ key: 1, commandId: ID, status: "completed" });
  });

  it("follows events after the REST answer and keeps the final state", () => {
    let log = commandAnswered(commandSent(EMPTY_LOG, 1), 1, ID);
    const states: string[] = [];

    for (const state of ["accepted", "completed", "accepted"]) {
      log = received(log, state);
      states.push(log.latest?.status ?? "none");
    }

    expect(states).toEqual(["accepted", "completed", "completed"]);
  });

  it("turns an unfinished command to unknown when the connection is lost", () => {
    const pending = commandAnswered(commandSent(EMPTY_LOG, 1), 1, ID);
    const completed = received(pending, "completed");

    expect(channelLost(pending).latest?.status).toBe("unknown");
    expect(channelLost(completed).latest?.status).toBe("completed");
  });

  it("drops the answer of a command that is no longer the latest", () => {
    const log = commandSent(commandSent(EMPTY_LOG, 1), 2);

    expect(commandAnswered(log, 1, ID).latest).toEqual({
      key: 2,
      commandId: null,
      status: "pending",
    });
  });

  it("refuses a lifecycle event outside the contract", () => {
    expect(
      lifecycleReceived(EMPTY_LOG, { command_id: ID, state: "exploded" }),
    ).toBeNull();
  });
});
