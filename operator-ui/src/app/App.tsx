import { useSyncExternalStore } from "react";
import { LoginForm } from "../features/session/LoginForm";
import { useI18n } from "../shared/i18n/I18nProvider";
import { LocaleSwitch } from "../shared/i18n/LocaleSwitch";
import type { OperatorStore } from "./operatorStore";
import { OperatorShell } from "./OperatorShell";

/** Nothing but the login form shows, and nothing is sent, before sign-in (REQ-HMI-002). */
export function App({ store }: { store: OperatorStore }) {
  const { t } = useI18n();
  const state = useSyncExternalStore(store.subscribe, store.getState);
  const { session } = state;

  switch (session.status) {
    case "checking":
      return (
        <main className="screen">
          <p>{t("hmi.session.checking")}</p>
          <LocaleSwitch />
        </main>
      );
    case "signed-out":
      return <LoginForm notice={session.notice} onSubmit={store.signIn} />;
    case "signed-in":
      return (
        <OperatorShell
          state={state}
          username={session.username}
          store={store}
        />
      );
  }
}
