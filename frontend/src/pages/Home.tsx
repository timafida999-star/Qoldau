import { useEffect, useMemo, useState } from "react";
import { Gift, LayoutGrid, Map as MapIcon } from "lucide-react";
import { Link } from "react-router-dom";

import { fetchListings } from "@/api/listings";
import { ListingCard } from "@/components/ListingCard";
import { MapView } from "@/components/MapView";
import { buttonVariants } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import type { Category, ListingStatus, ListingSummary } from "@/types";
import { CATEGORY_OPTIONS, STATUS_OPTIONS } from "@/utils/listingOptions";

type ViewMode = "grid" | "map";

export default function HomePage() {
  const { user } = useAuth();

  const [listings, setListings] = useState<ListingSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [view, setView] = useState<ViewMode>("grid");
  const [category, setCategory] = useState<Category | "all">("all");
  const [status, setStatus] = useState<ListingStatus | "all">("available");

  useEffect(() => {
    setIsLoading(true);
    fetchListings({
      category: category === "all" ? undefined : category,
      status: status === "all" ? undefined : status,
    })
      .then(setListings)
      .finally(() => setIsLoading(false));
  }, [category, status]);

  const hasListings = useMemo(() => listings.length > 0, [listings]);

  return (
    <div className="container py-10">
      <div className="mb-10 flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2 text-primary">
            <Gift className="h-6 w-6" />
            <span className="text-sm font-medium uppercase tracking-wide">Qoldau</span>
          </div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Find something useful nearby</h1>
          <p className="mt-1 text-muted-foreground">Everything here is free. Reserve it, meet up, done.</p>
        </div>

        {!user && (
          <Link to="/register" className={cn(buttonVariants({ size: "lg" }))}>
            Get started
          </Link>
        )}
      </div>

      <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-3">
          <Select value={category} onChange={(e) => setCategory(e.target.value as Category | "all")} className="w-44">
            <option value="all">All categories</option>
            {CATEGORY_OPTIONS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
          <Select value={status} onChange={(e) => setStatus(e.target.value as ListingStatus | "all")} className="w-40">
            {STATUS_OPTIONS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setView("grid")}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
              view === "grid" ? "border-primary bg-accent text-primary" : "border-input text-muted-foreground hover:bg-secondary"
            )}
          >
            <LayoutGrid className="h-4 w-4" />
            Grid
          </button>
          <button
            onClick={() => setView("map")}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
              view === "map" ? "border-primary bg-accent text-primary" : "border-input text-muted-foreground hover:bg-secondary"
            )}
          >
            <MapIcon className="h-4 w-4" />
            Map
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="py-24 text-center text-muted-foreground">Loading listings...</div>
      ) : !hasListings ? (
        <div className="rounded-xl border border-dashed border-border p-16 text-center text-muted-foreground">
          No listings match these filters yet.
        </div>
      ) : view === "grid" ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      ) : (
        <MapView listings={listings} />
      )}
    </div>
  );
}
