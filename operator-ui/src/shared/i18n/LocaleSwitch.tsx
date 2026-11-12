import { useI18n } from "./I18nProvider";
import { LOCALES, isLocale } from "./translate";

export function LocaleSwitch() {
  const { locale, setLocale, t } = useI18n();
  return (
    <label className="locale-switch">
      {t("hmi.locale.label")}
      <select
        value={locale}
        onChange={(event) => {
          if (isLocale(event.target.value)) setLocale(event.target.value);
        }}
      >
        {LOCALES.map((option) => (
          <option key={option} value={option}>
            {t(`hmi.locale.${option}`)}
          </option>
        ))}
      </select>
    </label>
  );
}
