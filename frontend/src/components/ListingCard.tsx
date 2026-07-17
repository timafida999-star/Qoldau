import { Link } from "react-router-dom";
import { ImageOff } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { API_BASE_URL } from "@/api/client";
import type { ListingSummary } from "@/types";
import { CATEGORY_LABELS, CONDITION_LABELS, STATUS_BADGE_VARIANT, STATUS_LABELS } from "@/utils/listingOptions";

export function ListingCard({ listing }: { listing: ListingSummary }) {
  const cover = listing.images[0];

  return (
    <Link to={`/listings/${listing.id}`}>
      <Card className="overflow-hidden">
        <div className="aspect-[4/3] w-full bg-secondary">
          {cover ? (
            <img
              src={`${API_BASE_URL}${cover.image_url}`}
              alt={listing.title}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-muted-foreground">
              <ImageOff className="h-8 w-8" />
            </div>
          )}
        </div>
        <CardContent className="space-y-2 p-4">
          <div className="flex items-start justify-between gap-2">
            <h3 className="line-clamp-1 font-medium">{listing.title}</h3>
            <Badge variant={STATUS_BADGE_VARIANT[listing.status]}>{STATUS_LABELS[listing.status]}</Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{CATEGORY_LABELS[listing.category]}</span>
            <span>&middot;</span>
            <span>{CONDITION_LABELS[listing.condition]}</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
