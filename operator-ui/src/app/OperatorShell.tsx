import { PhaseHeader } from "../features/phase/PhaseHeader";
import { useI18n } from "../shared/i18n/I18nProvider";
import { LocaleSwitch } from "../shared/i18n/LocaleSwitch";
import type { OperatorState } from "./operatorStore";

interface OperatorShellProps {
  state: OperatorState;
  username: string;
  onSignOut: () => Promise<void>;
}

/** Frame of every view after sign-in. */
export function OperatorShell({
  state,
  username,
  onSignOut,
}: OperatorShellProps) {
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
          <span>{username}</span>
          <LocaleSwitch />
          <button
            type="button"
            onClick={() => {
              void onSignOut();
            }}
          >
            {t("hmi.session.logout")}
          </button>
        </div>
      </header>
      <main className="shell-main" />
    </div>
  );
}
