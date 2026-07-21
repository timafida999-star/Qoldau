import { ChevronDown, Globe } from "lucide-react";
import { useTranslation } from "react-i18next";

import { SUPPORTED_LANGUAGES } from "@/i18n";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const current = (SUPPORTED_LANGUAGES as readonly string[]).includes(i18n.language)
    ? i18n.language
    : "en";

  return (
    <div className="relative inline-flex items-center">
      <Globe className="pointer-events-none absolute left-2.5 h-4 w-4 text-muted-foreground" />
      <select
        aria-label={t("language.label")}
        value={current}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
        className="h-9 cursor-pointer appearance-none rounded-lg border border-input bg-background py-1 pl-8 pr-8 text-sm font-medium text-foreground transition-colors hover:bg-secondary focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {SUPPORTED_LANGUAGES.map((lng) => (
          <option key={lng} value={lng}>
            {t(`language.${lng}`)}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2 h-4 w-4 text-muted-foreground" />
    </div>
  );
}
