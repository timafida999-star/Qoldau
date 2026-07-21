import { useEffect, useMemo, useState } from "react";
import { Gift, LayoutGrid, Loader2, Map as MapIcon, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { fetchListings } from "@/api/listings";
import { ListingCard } from "@/components/ListingCard";
import { ListingCardSkeleton } from "@/components/ListingCardSkeleton";
import { MapView } from "@/components/MapView";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import type { Category, ListingStatus, ListingSummary } from "@/types";
import { CATEGORY_VALUES, STATUS_VALUES } from "@/utils/listingOptions";

type ViewMode = "grid" | "map";

const PAGE_SIZE = 12;

export default function HomePage() {
  const { user } = useAuth();
  const { t } = useTranslation();

  const [listings, setListings] = useState<ListingSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [view, setView] = useState<ViewMode>("grid");
  const [category, setCategory] = useState<Category | "all">("all");
  const [status, setStatus] = useState<ListingStatus | "all">("available");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 350);
    return () => clearTimeout(timer);
  }, [search]);

  // Reset to the first page whenever a filter or the search term changes.
  useEffect(() => {
    let active = true;
    setIsLoading(true);
    fetchListings({
      category: category === "all" ? undefined : category,
      status: status === "all" ? undefined : status,
      search: debouncedSearch || undefined,
      page: 1,
      page_size: PAGE_SIZE,
    })
      .then((res) => {
        if (!active) return;
        setListings(res.items);
        setTotal(res.total);
        setHasMore(res.has_more);
        setPage(1);
      })
      .finally(() => active && setIsLoading(false));
    return () => {
      active = false;
    };
  }, [category, status, debouncedSearch]);

  async function loadMore() {
    const nextPage = page + 1;
    setIsLoadingMore(true);
    try {
      const res = await fetchListings({
        category: category === "all" ? undefined : category,
        status: status === "all" ? undefined : status,
        search: debouncedSearch || undefined,
        page: nextPage,
        page_size: PAGE_SIZE,
      });
      setListings((prev) => [...prev, ...res.items]);
      setHasMore(res.has_more);
      setPage(nextPage);
    } finally {
      setIsLoadingMore(false);
    }
  }

  const hasListings = useMemo(() => listings.length > 0, [listings]);

  return (
    <div>
      <section className="border-b border-border bg-gradient-to-b from-accent/50 to-background">
        <div className="container flex flex-col items-center py-16 text-center">
          <div className="flex items-center gap-2 text-primary">
            <Gift className="h-5 w-5" />
            <span className="text-sm font-medium uppercase tracking-wide">Qoldau</span>
          </div>
          <h1 className="mt-3 max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
            {t("home.title")}
          </h1>
          <p className="mt-3 max-w-xl text-muted-foreground">{t("home.subtitle")}</p>

          <div className="relative mt-8 w-full max-w-xl">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("home.searchPlaceholder")}
              className="h-12 rounded-full pl-12 pr-4 text-base shadow-soft"
            />
          </div>

          {!user && (
            <Link to="/register" className={cn(buttonVariants({ size: "lg" }), "mt-6")}>
              {t("home.getStarted")}
            </Link>
          )}
        </div>
      </section>

      <div className="container py-10">
        <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-3">
            <Select value={category} onChange={(e) => setCategory(e.target.value as Category | "all")} className="w-44">
              <option value="all">{t("home.allCategories")}</option>
              {CATEGORY_VALUES.map((value) => (
                <option key={value} value={value}>
                  {t(`category.${value}`)}
                </option>
              ))}
            </Select>
            <Select value={status} onChange={(e) => setStatus(e.target.value as ListingStatus | "all")} className="w-40">
              <option value="all">{t("home.allStatuses")}</option>
              {STATUS_VALUES.map((value) => (
                <option key={value} value={value}>
                  {t(`status.${value}`)}
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
              {t("home.grid")}
            </button>
            <button
              onClick={() => setView("map")}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
                view === "map" ? "border-primary bg-accent text-primary" : "border-input text-muted-foreground hover:bg-secondary"
              )}
            >
              <MapIcon className="h-4 w-4" />
              {t("home.map")}
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <ListingCardSkeleton key={i} />
            ))}
          </div>
        ) : !hasListings ? (
          <div className="rounded-xl border border-dashed border-border p-16 text-center text-muted-foreground">
            {t("home.empty")}
          </div>
        ) : view === "grid" ? (
          <>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {listings.map((listing) => (
                <ListingCard key={listing.id} listing={listing} />
              ))}
            </div>

            <div className="mt-10 flex flex-col items-center gap-3">
              <p className="text-sm text-muted-foreground">
                {t("home.showingCount", { shown: listings.length, total })}
              </p>
              {hasMore && (
                <Button variant="outline" size="lg" onClick={loadMore} disabled={isLoadingMore}>
                  {isLoadingMore && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {t("home.loadMore")}
                </Button>
              )}
            </div>
          </>
        ) : (
          <MapView listings={listings} />
        )}
      </div>
    </div>
  );
}
