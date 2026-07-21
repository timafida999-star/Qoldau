import { apiClient } from "./client";
import type { Report, ReportReason, ReportTargetType } from "@/types";

export async function createReport(
  targetType: ReportTargetType,
  targetId: string,
  reason: ReportReason,
  description?: string
): Promise<Report> {
  const { data } = await apiClient.post<Report>("/reports", {
    target_type: targetType,
    target_id: targetId,
    reason,
    description: description || undefined,
  });
  return data;
}

export async function fetchAdminReports(status?: "open" | "resolved"): Promise<Report[]> {
  const { data } = await apiClient.get<Report[]>("/admin/reports", { params: { status_filter: status } });
  return data;
}

export async function resolveReport(reportId: string): Promise<Report> {
  const { data } = await apiClient.patch<Report>(`/admin/reports/${reportId}`);
  return data;
}

export async function adminDeleteListing(listingId: string): Promise<void> {
  await apiClient.delete(`/admin/listings/${listingId}`);
}
