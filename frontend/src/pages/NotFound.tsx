import { useLocation, useNavigate } from "react-router-dom";
import { Compass, Home } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";

/**
 * Catch-all for unmatched routes. Without it an unknown URL rendered an empty
 * <main> - navbar and footer wrapped around nothing, which reads as a broken
 * page rather than a missing one.
 */
export default function NotFoundPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  return (
    <div className="container max-w-lg py-20 text-center">
      <Compass className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
      <p className="text-5xl font-semibold text-primary">404</p>
      <h1 className="mt-3 text-2xl font-semibold">{t("notFound.title")}</h1>
      <p className="mt-2 text-muted-foreground">{t("notFound.description")}</p>
      <p className="mt-4 break-all rounded-lg bg-secondary px-3 py-2 font-mono text-xs text-muted-foreground">
        {pathname}
      </p>
      <Button className="mt-6" onClick={() => navigate("/")}>
        <Home className="mr-2 h-4 w-4" />
        {t("notFound.backHome")}
      </Button>
    </div>
  );
}
