import {
  openPushChannel,
  type ChannelStatus,
  type PushChannel,
} from "../features/push/pushChannel";
import {
  closeSession,
  openSession,
  readSession,
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
}

/** What the HMI shows and the actions it takes; React reads it through useSyncExternalStore. */
export interface OperatorStore {
  getState: () => OperatorState;
  subscribe: (listener: () => void) => () => void;
  checkSession: () => Promise<void>;
  signIn: (credentials: Credentials) => Promise<void>;
  signOut: () => Promise<void>;
}

/** The push channel lives exactly as long as the session: opened on sign-in, closed on sign-out or once the session is refused (REQ-HMI-002, REQ-HMI-004). */
export function createOperatorStore(): OperatorStore {
  let state: OperatorState = {
    session: { status: "checking" },
    channel: "closed",
  };
  const listeners = new Set<() => void>();
  let channel: PushChannel | null = null;

  function update(next: Partial<OperatorState>) {
    state = { ...state, ...next };
    for (const listener of listeners) listener();
  }

  function enterSignedIn(username: string) {
    update({ session: { status: "signed-in", username } });
    channel = openPushChannel({
      onStatus: channelChanged,
      onMessage: () => undefined,
    });
  }

  function leaveSignedIn(notice: Notice | null) {
    channel?.close();
    channel = null;
    update({ session: { status: "signed-out", notice }, channel: "closed" });
  }

  function channelChanged(status: ChannelStatus) {
    update({ channel: status });
    if (status === "closed") void confirmSession();
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
