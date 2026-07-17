import { Link, useNavigate } from "react-router-dom";
import { Gift, Inbox, LogOut, PlusCircle, ShieldAlert, User as UserIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-primary">
          <Gift className="h-6 w-6" />
          Qoldau
        </Link>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate("/listings/new")}>
                <PlusCircle className="mr-2 h-4 w-4" />
                Give an item
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate("/reservations")}>
                <Inbox className="mr-2 h-4 w-4" />
                Reservations
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate(`/profile/${user.id}`)}>
                <UserIcon className="mr-2 h-4 w-4" />
                {user.full_name}
              </Button>
              {user.is_admin && (
                <Button variant="ghost" size="sm" onClick={() => navigate("/admin")}>
                  <ShieldAlert className="mr-2 h-4 w-4" />
                  Admin
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate("/login")}>
                Log in
              </Button>
              <Button size="sm" onClick={() => navigate("/register")}>
                Sign up
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
