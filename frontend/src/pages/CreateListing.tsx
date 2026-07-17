import { ListingForm } from "@/components/ListingForm";

export default function CreateListingPage() {
  return (
    <div className="container max-w-2xl py-12">
      <h1 className="mb-8 text-2xl font-semibold">Give an item away</h1>
      <ListingForm />
    </div>
  );
}
