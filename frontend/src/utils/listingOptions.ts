import type { Category, Condition, ListingStatus } from "@/types";

export const CATEGORY_LABELS: Record<Category, string> = {
  electronics: "Electronics",
  furniture: "Furniture",
  clothes: "Clothes",
  books: "Books",
  kitchen: "Kitchen",
  kids: "Kids",
  other: "Other",
};

export const CONDITION_LABELS: Record<Condition, string> = {
  new: "New",
  like_new: "Like new",
  good: "Good",
  fair: "Fair",
  worn: "Worn",
};

export const STATUS_LABELS: Record<ListingStatus, string> = {
  available: "Available",
  reserved: "Reserved",
  completed: "Completed",
};

export const STATUS_BADGE_VARIANT: Record<ListingStatus, "default" | "secondary" | "outline"> = {
  available: "default",
  reserved: "secondary",
  completed: "outline",
};

export const CATEGORY_OPTIONS = Object.entries(CATEGORY_LABELS) as [Category, string][];
export const CONDITION_OPTIONS = Object.entries(CONDITION_LABELS) as [Condition, string][];
export const STATUS_OPTIONS: ["all" | ListingStatus, string][] = [
  ["all", "All statuses"],
  ["available", STATUS_LABELS.available],
  ["reserved", STATUS_LABELS.reserved],
  ["completed", STATUS_LABELS.completed],
];
