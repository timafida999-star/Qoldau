import { Link } from "react-router-dom";
import { Clock, ImageOff, MapPin } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { API_BASE_URL } from "@/api/client";
import type { ListingSummary } from "@/types";
import { STATUS_BADGE_VARIANT } from "@/utils/listingOptions";
import { timeAgo } from "@/utils/time";

export function ListingCard({ listing }: { listing: ListingSummary }) {
  const { t, i18n } = useTranslation();
  const cover = listing.images[0];

  return (
    <Link to={`/listings/${listing.id}`} className="group block">
      <Card className="overflow-hidden transition-all duration-200 group-hover:-translate-y-1 group-hover:shadow-lg">
        <div className="relative aspect-[4/3] w-full overflow-hidden bg-secondary">
          {cover ? (
            <img
              src={`${API_BASE_URL}${cover.image_url}`}
              alt={listing.title}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-muted-foreground">
              <ImageOff className="h-8 w-8" />
            </div>
          )}
          <Badge
            variant={STATUS_BADGE_VARIANT[listing.status]}
            className="absolute right-3 top-3 shadow-sm backdrop-blur"
          >
            {t(`status.${listing.status}`)}
          </Badge>
        </div>
        <CardContent className="space-y-2 p-4">
          <h3 className="line-clamp-1 font-medium">{listing.title}</h3>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{t(`category.${listing.category}`)}</span>
            <span>&middot;</span>
            <span>{t(`condition.${listing.condition}`)}</span>
          </div>
          <div className="flex items-center justify-between gap-2 border-t border-border pt-2 text-xs text-muted-foreground">
            <span className="flex min-w-0 items-center gap-1">
              <MapPin className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{listing.address_text || t("listing.meetingLocation")}</span>
            </span>
            <span className="flex shrink-0 items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {timeAgo(listing.created_at, i18n.language)}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
