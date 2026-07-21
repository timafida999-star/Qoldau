import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { fetchListing } from "@/api/listings";
import { ListingForm } from "@/components/ListingForm";
import type { Listing } from "@/types";

export default function EditListingPage() {
  const { listingId } = useParams();
  const { t } = useTranslation();
  const [listing, setListing] = useState<Listing | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!listingId) return;
    fetchListing(listingId)
      .then(setListing)
      .finally(() => setLoading(false));
  }, [listingId]);

  if (loading) {
    return <div className="container py-16 text-center text-muted-foreground">{t("common.loading")}</div>;
  }

  if (!listing) {
    return <div className="container py-16 text-center text-muted-foreground">{t("listing.notFound")}</div>;
  }

  return (
    <div className="container max-w-2xl py-12">
      <h1 className="mb-8 text-2xl font-semibold">{t("editListing.title")}</h1>
      <ListingForm initialListing={listing} />
    </div>
  );
}
