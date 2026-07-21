import { Link } from "react-router-dom";
import { Gift } from "lucide-react";
import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export function Footer() {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  return (
    <footer className="mt-16 border-t border-border bg-secondary/40">
      <div className="container flex flex-col gap-6 py-10 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-xs">
          <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-primary">
            <Gift className="h-6 w-6" />
            Qoldau
          </Link>
          <p className="mt-3 text-sm text-muted-foreground">{t("footer.tagline")}</p>
        </div>

        <div className="flex flex-col gap-3 text-sm">
          <span className="font-medium text-foreground">{t("footer.explore")}</span>
          <Link to="/" className="text-muted-foreground transition-colors hover:text-primary">
            {t("footer.browse")}
          </Link>
          <Link to="/listings/new" className="text-muted-foreground transition-colors hover:text-primary">
            {t("nav.giveItem")}
          </Link>
        </div>

        <div className="flex flex-col items-start gap-3">
          <LanguageSwitcher />
        </div>
      </div>

      <div className="border-t border-border">
        <div className="container flex flex-col items-center justify-between gap-2 py-4 text-xs text-muted-foreground sm:flex-row">
          <span>{t("footer.rights", { year })}</span>
          <span>{t("footer.builtWith")}</span>
        </div>
      </div>
    </footer>
  );
}
