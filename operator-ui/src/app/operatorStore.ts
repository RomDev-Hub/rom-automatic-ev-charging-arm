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
}

/** What the HMI shows and the actions it takes; React reads it through useSyncExternalStore. */
export interface OperatorStore {
  getState: () => OperatorState;
  subscribe: (listener: () => void) => () => void;
  checkSession: () => Promise<void>;
  signIn: (credentials: Credentials) => Promise<void>;
  signOut: () => Promise<void>;
}

export function createOperatorStore(): OperatorStore {
  let state: OperatorState = { session: { status: "checking" } };
  const listeners = new Set<() => void>();

  function update(next: Partial<OperatorState>) {
    state = { ...state, ...next };
    for (const listener of listeners) listener();
  }

  function enterSignedIn(username: string) {
    update({ session: { status: "signed-in", username } });
  }

  function leaveSignedIn(notice: Notice | null) {
    update({ session: { status: "signed-out", notice } });
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
