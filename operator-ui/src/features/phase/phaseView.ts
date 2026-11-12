import type { components } from "../../shared/contracts/asyncapi";
import { isRecord } from "../../shared/isRecord";
import type { Unchecked } from "../push/pushChannel";

type Schemas = components["schemas"];

/** What the phase header shows; null is a value the telemetry did not give. */
export interface PhaseView {
  previous: string | null;
  current: string | null;
  expectedNext: string | null;
  sinceS: number | null;
}

export const UNKNOWN_PHASE: PhaseView = {
  previous: null,
  current: null,
  expectedNext: null,
  sinceS: null,
};

/** The phase block of a telemetry snapshot, pushed or read over REST; null when it breaks the contract. */
export function phaseFromTelemetry(
  data: Unchecked<Schemas["TelemetryData"]>,
): PhaseView | null {
  if (!isRecord(data.phase)) return null;
  const block: Unchecked<Schemas["PhaseBlock"] & Schemas["BlockUnavailable"]> =
    data.phase;
  if (block.unavailable === true) return UNKNOWN_PHASE;
  const {
    previous,
    phase,
    expected_next: expectedNext,
    since_s: sinceS,
  } = block;
  if (
    typeof previous !== "string" ||
    typeof phase !== "string" ||
    !isPhaseOrNull(expectedNext)
  ) {
    return null;
  }
  // The core sends a value it cannot measure as null (contracts/asyncapi.yaml).
  return {
    previous,
    current: phase,
    expectedNext,
    sinceS: typeof sinceS === "number" ? sinceS : null,
  };
}

/** The phases right after a phaseChanged event; the next snapshot brings the time in phase. */
export function phaseAfterChange(
  data: Unchecked<Schemas["PhaseChangedData"]>,
): PhaseView | null {
  const { previous, phase, expected_next: expectedNext } = data;
  if (
    typeof previous !== "string" ||
    typeof phase !== "string" ||
    !isPhaseOrNull(expectedNext)
  ) {
    return null;
  }
  return { previous, current: phase, expectedNext, sinceS: 0 };
}

function isPhaseOrNull(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
}
