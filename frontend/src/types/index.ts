export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  rating_avg: number;
  rating_count: number;
  is_admin: boolean;
  created_at: string;
}

export interface PublicUser {
  id: string;
  full_name: string;
  avatar_url?: string | null;
  bio?: string | null;
  rating_avg: number;
  rating_count: number;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface UserUpdateInput {
  full_name?: string;
  phone?: string;
  bio?: string;
}

export type Category =
  | "electronics"
  | "furniture"
  | "clothes"
  | "books"
  | "kitchen"
  | "kids"
  | "other";

export type Condition = "new" | "like_new" | "good" | "fair" | "worn";

export type ListingStatus = "available" | "reserved" | "completed";

export interface ListingImage {
  id: string;
  image_url: string;
  position: number;
}

export interface Listing {
  id: string;
  owner_id: string;
  owner: PublicUser;
  title: string;
  description: string;
  category: Category;
  condition: Condition;
  status: ListingStatus;
  latitude: number;
  longitude: number;
  address_text?: string | null;
  images: ListingImage[];
  created_at: string;
  updated_at: string;
}

export interface ListingSummary {
  id: string;
  title: string;
  category: Category;
  condition: Condition;
  status: ListingStatus;
  latitude: number;
  longitude: number;
  images: ListingImage[];
  created_at: string;
}

export type ReservationStatus = "pending" | "accepted" | "declined" | "cancelled";

export interface ListingBrief {
  id: string;
  title: string;
  status: ListingStatus;
}

export interface Reservation {
  id: string;
  listing: ListingBrief;
  requester: PublicUser;
  status: ReservationStatus;
  chat_id: string | null;
  exchange_id: string | null;
  created_at: string;
  updated_at: string;
  role: "owner" | "requester";
}

export interface ChatMessage {
  id: string;
  chat_id: string;
  sender_id: string;
  content: string;
  created_at: string;
}

export interface ChatInfo {
  id: string;
  reservation_id: string;
  listing_title: string;
  other_participant: PublicUser;
  created_at: string;
}

export type ExchangeStatus = "pending" | "completed";

export interface Exchange {
  id: string;
  reservation_id: string;
  status: ExchangeStatus;
  completed_at: string | null;
  created_at: string;
  listing_id: string;
  listing_title: string;
  owner_id: string;
  requester_id: string;
  role: "owner" | "requester";
}

export interface Review {
  id: string;
  exchange_id: string;
  reviewer: PublicUser;
  reviewee_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
}

export type ReportTargetType = "listing" | "user";
export type ReportReason = "spam" | "inappropriate" | "fraud" | "other";
export type ReportStatus = "open" | "resolved";

export interface Report {
  id: string;
  reporter: PublicUser;
  target_type: ReportTargetType;
  target_id: string;
  reason: ReportReason;
  description: string | null;
  status: ReportStatus;
  created_at: string;
}
