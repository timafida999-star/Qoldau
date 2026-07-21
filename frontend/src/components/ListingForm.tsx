import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

import { createListing, deleteListingImage, updateListing, uploadListingImages } from "@/api/listings";
import { API_BASE_URL } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { MapPicker } from "@/components/MapPicker";
import type { Category, Condition, Listing } from "@/types";
import { CATEGORY_VALUES, CONDITION_VALUES } from "@/utils/listingOptions";

type ListingFormValues = {
  title: string;
  description: string;
  category: Category;
  condition: Condition;
  address_text?: string;
};

const DEFAULT_CENTER: [number, number] = [51.169392, 71.449074]; // Astana

interface ListingFormProps {
  initialListing?: Listing;
}

export function ListingForm({ initialListing }: ListingFormProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const isEdit = Boolean(initialListing);

  const listingSchema = z.object({
    title: z.string().min(3, t("form.shortTitle")).max(120),
    description: z.string().min(10, t("form.shortDescription")),
    category: z.enum(["electronics", "furniture", "clothes", "books", "kitchen", "kids", "other"]),
    condition: z.enum(["new", "like_new", "good", "fair", "worn"]),
    address_text: z.string().optional(),
  });

  const [position, setPosition] = useState<[number, number]>(
    initialListing ? [initialListing.latitude, initialListing.longitude] : DEFAULT_CENTER
  );
  const [files, setFiles] = useState<File[]>([]);
  const [existingImages, setExistingImages] = useState(initialListing?.images ?? []);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ListingFormValues>({
    resolver: zodResolver(listingSchema),
    defaultValues: initialListing
      ? {
          title: initialListing.title,
          description: initialListing.description,
          category: initialListing.category,
          condition: initialListing.condition,
          address_text: initialListing.address_text ?? "",
        }
      : { category: "other", condition: "good" },
  });

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files ? Array.from(e.target.files) : [];
    setFiles((prev) => [...prev, ...selected]);
  }

  function removeSelectedFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function removeExistingImage(imageId: string) {
    if (!initialListing) return;
    await deleteListingImage(initialListing.id, imageId);
    setExistingImages((prev) => prev.filter((img) => img.id !== imageId));
  }

  async function onSubmit(values: ListingFormValues) {
    setError(null);
    try {
      const payload = {
        ...values,
        latitude: position[0],
        longitude: position[1],
      };

      let listing: Listing;
      if (isEdit && initialListing) {
        listing = await updateListing(initialListing.id, payload);
      } else {
        listing = await createListing(payload);
      }

      if (files.length > 0) {
        await uploadListingImages(listing.id, files);
      }

      navigate(`/listings/${listing.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || t("common.somethingWrong"));
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="title">{t("form.title")}</Label>
        <Input id="title" placeholder={t("form.titlePlaceholder")} {...register("title")} />
        {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">{t("form.description")}</Label>
        <Textarea
          id="description"
          placeholder={t("form.descriptionPlaceholder")}
          {...register("description")}
        />
        {errors.description && <p className="text-sm text-destructive">{errors.description.message}</p>}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="category">{t("form.category")}</Label>
          <Select id="category" {...register("category")}>
            {CATEGORY_VALUES.map((value) => (
              <option key={value} value={value}>
                {t(`category.${value}`)}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="condition">{t("form.condition")}</Label>
          <Select id="condition" {...register("condition")}>
            {CONDITION_VALUES.map((value) => (
              <option key={value} value={value}>
                {t(`condition.${value}`)}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="address_text">{t("form.addressLabel")}</Label>
        <Input id="address_text" placeholder={t("form.addressPlaceholder")} {...register("address_text")} />
      </div>

      <div className="space-y-2">
        <Label>{t("form.location")}</Label>
        <MapPicker
          latitude={position[0]}
          longitude={position[1]}
          onChange={(lat, lng) => setPosition([lat, lng])}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="images">{t("form.photos")}</Label>
        <Input id="images" type="file" accept="image/*" multiple onChange={handleFileChange} />

        {existingImages.length > 0 && (
          <div className="flex flex-wrap gap-3 pt-2">
            {existingImages.map((img) => (
              <div key={img.id} className="relative h-20 w-20 overflow-hidden rounded-lg border border-border">
                <img src={`${API_BASE_URL}${img.image_url}`} alt="" className="h-full w-full object-cover" />
                <button
                  type="button"
                  onClick={() => removeExistingImage(img.id)}
                  className="absolute right-1 top-1 rounded-full bg-background/90 p-0.5 shadow-sm"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {files.length > 0 && (
          <div className="flex flex-wrap gap-3 pt-2">
            {files.map((file, index) => (
              <div key={index} className="relative h-20 w-20 overflow-hidden rounded-lg border border-border">
                <img src={URL.createObjectURL(file)} alt="" className="h-full w-full object-cover" />
                <button
                  type="button"
                  onClick={() => removeSelectedFile(index)}
                  className="absolute right-1 top-1 rounded-full bg-background/90 p-0.5 shadow-sm"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Button type="submit" size="lg" disabled={isSubmitting}>
        {isSubmitting ? t("common.saving") : isEdit ? t("common.saveChanges") : t("form.publish")}
      </Button>
    </form>
  );
}
