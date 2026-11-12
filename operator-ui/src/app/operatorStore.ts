import {
  phaseAfterChange,
  phaseFromTelemetry,
  UNKNOWN_PHASE,
  type PhaseView,
} from "../features/phase/phaseView";
import { RateMeter } from "../features/phase/rateMeter";
import {
  ignoreMessage,
  openPushChannel,
  PHASE_CHANGED,
  TELEMETRY_SNAPSHOT,
  type ChannelStatus,
  type PushChannel,
  type PushEnvelope,
} from "../features/push/pushChannel";
import {
  closeSession,
  openSession,
  readSession,
  readTelemetry,
  SESSION_REQUIRED,
  type Credentials,
  type Notice,
} from "../shared/api/rest";

export type SessionState =
  | { status: "checking" }
  | { status: "signed-out"; notice: Notice | null }
  | { status: "signed-in"; username: string };

export interface OperatorState {
  session: SessionState;
  channel: ChannelStatus;
  phase: PhaseView;
  telemetryHz: number;
}

/** What the HMI shows and the actions it takes; React reads it through useSyncExternalStore. */
export interface OperatorStore {
  getState: () => OperatorState;
  subscribe: (listener: () => void) => () => void;
  checkSession: () => Promise<void>;
  signIn: (credentials: Credentials) => Promise<void>;
  signOut: () => Promise<void>;
}

const SIGNED_OUT = {
  channel: "closed",
  phase: UNKNOWN_PHASE,
  telemetryHz: 0,
} as const satisfies Partial<OperatorState>;
// The rate falls to 0 within this period once snapshots stop coming.
const RATE_REFRESH_MS = 500;

/** The push channel lives exactly as long as the session: opened on sign-in, closed on sign-out or once the session is refused (REQ-HMI-002, REQ-HMI-004). */
export function createOperatorStore(): OperatorStore {
  let state: OperatorState = { session: { status: "checking" }, ...SIGNED_OUT };
  const listeners = new Set<() => void>();
  const rate = new RateMeter();
  let channel: PushChannel | null = null;
  let rateTimer: ReturnType<typeof setInterval> | undefined;

  function update(next: Partial<OperatorState>) {
    state = { ...state, ...next };
    for (const listener of listeners) listener();
  }

  function enterSignedIn(username: string) {
    update({ session: { status: "signed-in", username } });
    channel = openPushChannel({
      onStatus: channelChanged,
      onMessage: messageReceived,
    });
    rateTimer = setInterval(refreshRate, RATE_REFRESH_MS);
  }

  function leaveSignedIn(notice: Notice | null) {
    channel?.close();
    channel = null;
    clearInterval(rateTimer);
    rate.clear();
    update({ session: { status: "signed-out", notice }, ...SIGNED_OUT });
  }

  function channelChanged(status: ChannelStatus) {
    update({ channel: status });
    if (status === "open") void readSnapshot();
    if (status === "closed") void confirmSession();
  }

  // After each (re)connection the latest snapshot is read over REST (contracts/asyncapi.yaml, REQ-GW-019).
  async function readSnapshot() {
    const asked = channel;
    const result = await readTelemetry();
    if (channel !== asked) return;
    if (!result.ok) {
      if (result.notice.code === SESSION_REQUIRED) leaveSignedIn(result.notice);
      return;
    }
    const phase = phaseFromTelemetry(result.data);
    if (phase) update({ phase });
  }

  // A closed connection may mean the session ended, e.g. after a core restart; the handshake itself does not say why.
  async function confirmSession() {
    const asked = channel;
    const result = await readSession();
    if (
      channel === asked &&
      !result.ok &&
      result.notice.code === SESSION_REQUIRED
    ) {
      leaveSignedIn(result.notice);
    }
  }

  function messageReceived({ type, data }: PushEnvelope) {
    if (type === TELEMETRY_SNAPSHOT) telemetryReceived(data);
    else if (type === PHASE_CHANGED) phaseChanged(data);
  }

  function telemetryReceived(data: PushEnvelope["data"]) {
    const phase = phaseFromTelemetry(data);
    if (phase === null) {
      ignoreMessage(data);
      return;
    }
    rate.record(performance.now());
    update({ phase, telemetryHz: rate.rateHz(performance.now()) });
  }

  function phaseChanged(data: PushEnvelope["data"]) {
    const phase = phaseAfterChange(data);
    if (phase === null) ignoreMessage(data);
    else update({ phase });
  }

  function refreshRate() {
    const telemetryHz = rate.rateHz(performance.now());
    if (telemetryHz !== state.telemetryHz) update({ telemetryHz });
  }

  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    async checkSession() {
      const result = await readSession();
      if (result.ok) enterSignedIn(result.data.username);
      else
        leaveSignedIn(
          result.notice.code === SESSION_REQUIRED ? null : result.notice,
        );
    },
    async signIn(credentials) {
      const result = await openSession(credentials);
      if (result.ok) enterSignedIn(result.data.username);
      else leaveSignedIn(result.notice);
    },
    async signOut() {
      leaveSignedIn(null);
      await closeSession();
    },
  };
}
