import { apiClient } from "./client";
import type { Exchange } from "@/types";

export async function fetchExchange(exchangeId: string): Promise<Exchange> {
  const { data } = await apiClient.get<Exchange>(`/exchanges/${exchangeId}`);
  return data;
}

export async function fetchExchangeQrImage(exchangeId: string): Promise<string> {
  const { data } = await apiClient.get(`/exchanges/${exchangeId}/qr`, { responseType: "blob" });
  return URL.createObjectURL(data as Blob);
}

export async function verifyExchange(qrUuid: string): Promise<Exchange> {
  const { data } = await apiClient.post<Exchange>("/exchanges/verify", { qr_uuid: qrUuid });
  return data;
}
