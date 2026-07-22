import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { fetchListings, type ListingFilters } from "@/api/listings";
import { ListingCard } from "@/components/ListingCard";
import { ListingCardSkeleton } from "@/components/ListingCardSkeleton";
import { Button } from "@/components/ui/button";
import type { ListingSummary } from "@/types";

const PAGE_SIZE = 6;

interface ListingGridProps {
  /** Base filters (e.g. owner + status). Pagination is handled internally. */
  filters: ListingFilters;
  emptyText: string;
}

/** A self-contained, paginated grid of listings — used by the profile tabs. */
export function ListingGrid({ filters, emptyText }: ListingGridProps) {
  const { t } = useTranslation();
  const [items, setItems] = useState<ListingSummary[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const filterKey = JSON.stringify(filters);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchListings({ ...filters, page: 1, page_size: PAGE_SIZE })
      .then((res) => {
        if (!active) return;
        setItems(res.items);
        setHasMore(res.has_more);
        setPage(1);
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey]);

  async function loadMore() {
    const next = page + 1;
    setLoadingMore(true);
    try {
      const res = await fetchListings({ ...filters, page: next, page_size: PAGE_SIZE });
      setItems((prev) => [...prev, ...res.items]);
      setHasMore(res.has_more);
      setPage(next);
    } finally {
      setLoadingMore(false);
    }
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <ListingCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-border p-10 text-center text-muted-foreground">
        {emptyText}
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {items.map((listing) => (
          <ListingCard key={listing.id} listing={listing} />
        ))}
      </div>
      {hasMore && (
        <div className="flex justify-center">
          <Button variant="outline" onClick={loadMore} disabled={loadingMore}>
            {loadingMore && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {t("home.loadMore")}
          </Button>
        </div>
      )}
    </div>
  );
}
