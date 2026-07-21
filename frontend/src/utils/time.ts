const DIVISIONS: { amount: number; unit: Intl.RelativeTimeFormatUnit }[] = [
  { amount: 60, unit: "second" },
  { amount: 60, unit: "minute" },
  { amount: 24, unit: "hour" },
  { amount: 7, unit: "day" },
  { amount: 4.34524, unit: "week" },
  { amount: 12, unit: "month" },
  { amount: Number.POSITIVE_INFINITY, unit: "year" },
];

/**
 * Kazakh unit names.
 *
 * Browsers report `kk` as supported by Intl.RelativeTimeFormat but ship no
 * relative-time data for it, so it renders raw fallbacks like "-1 min".
 * Kazakh keeps the noun singular after a numeral, so one word per unit is
 * grammatically correct for every count.
 */
const KK_UNITS: Record<string, string> = {
  second: "секунд",
  minute: "минут",
  hour: "сағат",
  day: "күн",
  week: "апта",
  month: "ай",
  year: "жыл",
};

/** Localized "2 days ago" style string based on the active language. */
export function timeAgo(iso: string, locale: string): string {
  let duration = (new Date(iso).getTime() - Date.now()) / 1000;

  for (const division of DIVISIONS) {
    if (Math.abs(duration) < division.amount) {
      const value = Math.round(duration);

      if (locale.startsWith("kk")) {
        return `${Math.abs(value)} ${KK_UNITS[division.unit]} бұрын`;
      }

      return new Intl.RelativeTimeFormat(locale, { numeric: "auto" }).format(value, division.unit);
    }
    duration /= division.amount;
  }
  return "";
}
