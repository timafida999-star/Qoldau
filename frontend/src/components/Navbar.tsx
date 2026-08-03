import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Gift, Inbox, LogOut, Menu, PlusCircle, ShieldAlert, User as UserIcon, X } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { NotificationBell } from "@/components/NotificationBell";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/hooks/useAuth";

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { t } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);

  // Whatever caused the route change (menu item, a link under the panel,
  // browser back), an open mobile menu must not survive it.
  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  function go(path: string) {
    setMenuOpen(false);
    navigate(path);
  }

  function handleLogout() {
    setMenuOpen(false);
    logout();
    navigate("/");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-primary" onClick={() => setMenuOpen(false)}>
          <Gift className="h-6 w-6" />
          Qoldau
        </Link>

        {/* Desktop */}
        <div className="hidden items-center gap-3 md:flex">
          {user ? (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate("/listings/new")}>
                <PlusCircle className="mr-2 h-4 w-4" />
                {t("nav.giveItem")}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate("/reservations")}>
                <Inbox className="mr-2 h-4 w-4" />
                {t("nav.reservations")}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate(`/profile/${user.id}`)}>
                <UserIcon className="mr-2 h-4 w-4" />
                {user.full_name}
              </Button>
              {user.is_admin && (
                <Button variant="ghost" size="sm" onClick={() => navigate("/admin")}>
                  <ShieldAlert className="mr-2 h-4 w-4" />
                  {t("nav.admin")}
                </Button>
              )}
              <NotificationBell />
              <ThemeToggle />
              <LanguageSwitcher />
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                {t("nav.logout")}
              </Button>
            </>
          ) : (
            <>
              <ThemeToggle />
              <LanguageSwitcher />
              <Button variant="ghost" size="sm" onClick={() => navigate("/login")}>
                {t("nav.login")}
              </Button>
              <Button size="sm" onClick={() => navigate("/register")}>
                {t("nav.signup")}
              </Button>
            </>
          )}
        </div>

        {/* Mobile: keep the bell visible, everything else folds into the menu */}
        <div className="flex items-center gap-1 md:hidden">
          {user && <NotificationBell />}
          <Button
            variant="ghost"
            size="icon"
            aria-label={t("nav.menu")}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {menuOpen && (
        <div className="border-t border-border bg-background md:hidden">
          <div className="container flex flex-col gap-1 py-3">
            {user ? (
              <>
                <Button variant="ghost" className="justify-start" onClick={() => go("/listings/new")}>
                  <PlusCircle className="mr-2 h-4 w-4" />
                  {t("nav.giveItem")}
                </Button>
                <Button variant="ghost" className="justify-start" onClick={() => go("/reservations")}>
                  <Inbox className="mr-2 h-4 w-4" />
                  {t("nav.reservations")}
                </Button>
                <Button variant="ghost" className="justify-start" onClick={() => go(`/profile/${user.id}`)}>
                  <UserIcon className="mr-2 h-4 w-4" />
                  {user.full_name}
                </Button>
                {user.is_admin && (
                  <Button variant="ghost" className="justify-start" onClick={() => go("/admin")}>
                    <ShieldAlert className="mr-2 h-4 w-4" />
                    {t("nav.admin")}
                  </Button>
                )}
                <div className="my-2 flex items-center gap-2 border-t border-border pt-3">
                  <ThemeToggle />
                  <LanguageSwitcher />
                </div>
                <Button variant="outline" className="justify-start" onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  {t("nav.logout")}
                </Button>
              </>
            ) : (
              <>
                <div className="mb-2 flex items-center gap-2">
                  <ThemeToggle />
                  <LanguageSwitcher />
                </div>
                <Button variant="ghost" className="justify-start" onClick={() => go("/login")}>
                  {t("nav.login")}
                </Button>
                <Button className="justify-start" onClick={() => go("/register")}>
                  {t("nav.signup")}
                </Button>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
