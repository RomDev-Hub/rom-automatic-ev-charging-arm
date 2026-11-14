import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  DEFAULT_LOCALE,
  isLocale,
  translate,
  type Locale,
  type Params,
} from "./translate";

const STORAGE_KEY = "ev-arm.locale";

export interface I18n {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Params) => string;
}

const I18nContext = createContext<I18n | null>(null);

function rememberedLocale(): Locale {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return isLocale(stored) ? stored : DEFAULT_LOCALE;
  } catch {
    // Storage blocked by the browser: the default language applies.
    return DEFAULT_LOCALE;
  }
}

/** Language of the HMI, switchable at run time and remembered in this browser (REQ-I18N-007). */
export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setCurrentLocale] = useState(rememberedLocale);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.title = translate(locale, "hmi.app.title");
  }, [locale]);

  const i18n = useMemo<I18n>(
    () => ({
      locale,
      setLocale(next) {
        setCurrentLocale(next);
        try {
          localStorage.setItem(STORAGE_KEY, next);
        } catch {
          // Storage blocked by the browser: the choice holds until the page reloads.
        }
      },
      t: (key, params) => translate(locale, key, params),
    }),
    [locale],
  );

  return <I18nContext value={i18n}>{children}</I18nContext>;
}

export function useI18n(): I18n {
  const i18n = useContext(I18nContext);
  if (i18n === null) throw new Error("useI18n needs an I18nProvider above it");
  return i18n;
}
