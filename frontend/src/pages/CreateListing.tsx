import { useTranslation } from "react-i18next";

import { ListingForm } from "@/components/ListingForm";

export default function CreateListingPage() {
  const { t } = useTranslation();

  return (
    <div className="container max-w-2xl py-12">
      <h1 className="mb-8 text-2xl font-semibold">{t("createListing.title")}</h1>
      <ListingForm />
    </div>
  );
}
