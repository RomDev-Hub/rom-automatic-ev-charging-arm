import { useI18n } from "../shared/i18n/I18nProvider";
import { LocaleSwitch } from "../shared/i18n/LocaleSwitch";

export function App() {
  const { t } = useI18n();
  return (
    <main className="screen">
      <h1>{t("hmi.app.title")}</h1>
      <LocaleSwitch />
    </main>
  );
}
