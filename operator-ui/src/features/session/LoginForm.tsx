import { useState } from "react";
import type { Credentials, Notice } from "../../shared/api/rest";
import { useI18n } from "../../shared/i18n/I18nProvider";
import { LocaleSwitch } from "../../shared/i18n/LocaleSwitch";

interface LoginFormProps {
  notice: Notice | null;
  onSubmit: (credentials: Credentials) => Promise<void>;
}

/** Credentials go only into the body of the session request, never into storage or the URL (REQ-HMI-002). */
export function LoginForm({ notice, onSubmit }: LoginFormProps) {
  const { t } = useI18n();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  return (
    <main className="screen">
      <h1>{t("hmi.app.title")}</h1>
      <form
        className="login-form"
        onSubmit={(event) => {
          event.preventDefault();
          setSubmitting(true);
          void onSubmit({ username, password }).finally(() => {
            setSubmitting(false);
            setPassword("");
          });
        }}
      >
        <label className="field">
          {t("hmi.login.username")}
          <input
            autoComplete="username"
            required
            value={username}
            onChange={(event) => {
              setUsername(event.target.value);
            }}
          />
        </label>
        <label className="field">
          {t("hmi.login.password")}
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
            }}
          />
        </label>
        {notice && (
          <p className="notice" role="alert">
            {t(notice.code, notice.params)}
          </p>
        )}
        <button type="submit" disabled={submitting}>
          {t("hmi.login.submit")}
        </button>
      </form>
      <LocaleSwitch />
    </main>
  );
}
