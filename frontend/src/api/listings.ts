import { apiClient } from "./client";
import type { Category, Condition, Listing, ListingStatus, ListingSummary } from "@/types";

export interface ListingFilters {
  category?: Category;
  status?: ListingStatus;
}

export interface ListingInput {
  title: string;
  description: string;
  category: Category;
  condition: Condition;
  latitude: number;
  longitude: number;
  address_text?: string;
}

export async function fetchListings(filters: ListingFilters = {}): Promise<ListingSummary[]> {
  const { data } = await apiClient.get<ListingSummary[]>("/listings", { params: filters });
  return data;
}

export async function fetchListing(id: string): Promise<Listing> {
  const { data } = await apiClient.get<Listing>(`/listings/${id}`);
  return data;
}

export async function createListing(input: ListingInput): Promise<Listing> {
  const { data } = await apiClient.post<Listing>("/listings", input);
  return data;
}

export async function updateListing(id: string, input: Partial<ListingInput>): Promise<Listing> {
  const { data } = await apiClient.patch<Listing>(`/listings/${id}`, input);
  return data;
}

export async function deleteListing(id: string): Promise<void> {
  await apiClient.delete(`/listings/${id}`);
}

export async function uploadListingImages(id: string, files: File[]) {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  const { data } = await apiClient.post(`/listings/${id}/images`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteListingImage(listingId: string, imageId: string): Promise<void> {
  await apiClient.delete(`/listings/${listingId}/images/${imageId}`);
}
