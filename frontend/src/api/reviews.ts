import { apiClient } from "./client";
import type { Review } from "@/types";

export async function createReview(exchangeId: string, rating: number, comment?: string): Promise<Review> {
  const { data } = await apiClient.post<Review>("/reviews", {
    exchange_id: exchangeId,
    rating,
    comment: comment || undefined,
  });
  return data;
}

export async function fetchUserReviews(userId: string): Promise<Review[]> {
  const { data } = await apiClient.get<Review[]>(`/users/${userId}/reviews`);
  return data;
}
