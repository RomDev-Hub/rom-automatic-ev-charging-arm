import { PhaseHeader } from "../features/phase/PhaseHeader";
import { StopButton } from "../features/stop/StopButton";
import { useI18n } from "../shared/i18n/I18nProvider";
import { LocaleSwitch } from "../shared/i18n/LocaleSwitch";
import { Toast } from "../shared/Toast";
import type { OperatorState, OperatorStore } from "./operatorStore";

interface OperatorShellProps {
  state: OperatorState;
  username: string;
  store: OperatorStore;
}

/** Frame of every view after sign-in: phases, Stop and session controls on top. */
export function OperatorShell({ state, username, store }: OperatorShellProps) {
  const { t } = useI18n();
  return (
    <div className="shell">
      <header className="shell-header">
        <PhaseHeader
          phase={state.phase}
          channel={state.channel}
          telemetryHz={state.telemetryHz}
        />
        <div className="shell-session">
          <StopButton command={state.commands.latest} onStop={store.stop} />
          <span>{username}</span>
          <LocaleSwitch />
          <button
            type="button"
            onClick={() => {
              void store.signOut();
            }}
          >
            {t("hmi.session.logout")}
          </button>
        </div>
      </header>
      <main className="shell-main" />
      <Toast toast={state.toast} onDismiss={store.dismissToast} />
    </div>
  );
}
