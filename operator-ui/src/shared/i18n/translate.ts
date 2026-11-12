import en from "../../../../robot-core/src/robot_core/locales/en.json";
import vi from "../../../../robot-core/src/robot_core/locales/vi.json";
import { MISSING } from "../format";

export const LOCALES = ["vi", "en"] as const;
export type Locale = (typeof LOCALES)[number];
/** Shown until the operator picks a language (REQ-I18N-003). */
export const DEFAULT_LOCALE: Locale = "vi";

export type Params = Readonly<Record<string, unknown>>;

const MESSAGES: Readonly<Record<Locale, Readonly<Record<string, string>>>> = {
  vi,
  en,
};
const PLACEHOLDER = /\{(\w+)\}/g;
const warnedKeys = new Set<string>();

export function isLocale(value: unknown): value is Locale {
  return LOCALES.some((locale) => locale === value);
}

/** The message of `key`, `{name}` placeholders filled; a missing key shows as itself with one developer warning (REQ-I18N-006). */
export function translate(
  locale: Locale,
  key: string,
  params: Params = {},
): string {
  const message = MESSAGES[locale][key];
  if (message === undefined) {
    if (!warnedKeys.has(`${locale}:${key}`)) {
      warnedKeys.add(`${locale}:${key}`);
      console.warn(`no ${locale} message for the locale key "${key}"`);
    }
    return key;
  }
  return message.replace(PLACEHOLDER, (placeholder, name: string) =>
    name in params ? formatParam(params[name]) : placeholder,
  );
}

function formatParam(value: unknown): string {
  if (Array.isArray(value)) return value.map(formatParam).join(", ");
  if (typeof value === "string") return value;
  if (typeof value === "number")
    return Number.isFinite(value) ? String(value) : MISSING;
  if (typeof value === "boolean") return String(value);
  return value === null || value === undefined
    ? MISSING
    : JSON.stringify(value);
}
