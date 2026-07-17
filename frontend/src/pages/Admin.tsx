import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Check, ShieldAlert, Trash2 } from "lucide-react";

import { adminDeleteListing, fetchAdminReports, resolveReport } from "@/api/reports";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Report } from "@/types";

const REASON_LABELS: Record<Report["reason"], string> = {
  spam: "Spam",
  inappropriate: "Inappropriate content",
  fraud: "Fraud or scam",
  other: "Other",
};

export default function AdminPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [tab, setTab] = useState<"open" | "resolved">("open");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await fetchAdminReports(tab);
      setReports(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  async function handleResolve(reportId: string) {
    setBusyId(reportId);
    try {
      await resolveReport(reportId);
      await load();
    } finally {
      setBusyId(null);
    }
  }

  async function handleDeleteListing(report: Report) {
    if (!confirm("Delete this listing? This cannot be undone.")) return;
    setBusyId(report.id);
    try {
      await adminDeleteListing(report.target_id);
      await resolveReport(report.id);
      await load();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="container max-w-3xl py-10">
      <h1 className="mb-6 flex items-center gap-2 text-2xl font-semibold">
        <ShieldAlert className="h-6 w-6 text-primary" />
        Admin — Reports
      </h1>

      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setTab("open")}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            tab === "open" ? "bg-accent text-primary" : "text-muted-foreground hover:bg-secondary"
          }`}
        >
          Open
        </button>
        <button
          onClick={() => setTab("resolved")}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            tab === "resolved" ? "bg-accent text-primary" : "text-muted-foreground hover:bg-secondary"
          }`}
        >
          Resolved
        </button>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : reports.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border p-10 text-center text-muted-foreground">
          No {tab} reports.
        </p>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <Card key={report.id}>
              <CardContent className="space-y-3 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{report.target_type}</Badge>
                      <Badge variant="secondary">{REASON_LABELS[report.reason]}</Badge>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Reported by {report.reporter.full_name} &middot;{" "}
                      {new Date(report.created_at).toLocaleDateString()}
                    </p>
                    {report.description && <p className="mt-2 text-sm text-foreground/90">{report.description}</p>}
                    <Link
                      to={report.target_type === "listing" ? `/listings/${report.target_id}` : `/profile/${report.target_id}`}
                      className="mt-2 inline-block text-sm font-medium text-primary hover:underline"
                    >
                      View {report.target_type}
                    </Link>
                  </div>
                </div>

                {tab === "open" && (
                  <div className="flex gap-2 border-t border-border pt-3">
                    <Button size="sm" disabled={busyId === report.id} onClick={() => handleResolve(report.id)}>
                      <Check className="mr-1 h-4 w-4" />
                      Resolve
                    </Button>
                    {report.target_type === "listing" && (
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={busyId === report.id}
                        onClick={() => handleDeleteListing(report)}
                      >
                        <Trash2 className="mr-1 h-4 w-4" />
                        Delete listing
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
