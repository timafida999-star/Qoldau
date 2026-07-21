import type { Category, Condition, ListingStatus } from "@/types";

export const CATEGORY_VALUES: Category[] = [
  "electronics",
  "furniture",
  "clothes",
  "books",
  "kitchen",
  "kids",
  "other",
];

export const CONDITION_VALUES: Condition[] = ["new", "like_new", "good", "fair", "worn"];

export const STATUS_VALUES: ListingStatus[] = ["available", "reserved", "completed"];

export const STATUS_BADGE_VARIANT: Record<ListingStatus, "default" | "secondary" | "outline"> = {
  available: "default",
  reserved: "secondary",
  completed: "outline",
};
