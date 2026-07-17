import { apiClient } from "./client";
import type { Reservation } from "@/types";

export async function createReservation(listingId: string): Promise<Reservation> {
  const { data } = await apiClient.post<Reservation>(`/listings/${listingId}/reservations`);
  return data;
}

export async function listMyReservations(): Promise<Reservation[]> {
  const { data } = await apiClient.get<Reservation[]>("/reservations/mine");
  return data;
}

export async function actOnReservation(
  reservationId: string,
  action: "accept" | "decline" | "cancel"
): Promise<Reservation> {
  const { data } = await apiClient.patch<Reservation>(`/reservations/${reservationId}`, { action });
  return data;
}
