import { useI18n } from "../shared/i18n/I18nProvider";
import { LocaleSwitch } from "../shared/i18n/LocaleSwitch";

interface OperatorShellProps {
  username: string;
  onSignOut: () => Promise<void>;
}

/** Frame of every view after sign-in. */
export function OperatorShell({ username, onSignOut }: OperatorShellProps) {
  const { t } = useI18n();
  return (
    <div className="shell">
      <header className="shell-header">
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
