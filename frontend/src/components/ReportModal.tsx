import { useState } from "react";
import { Flag } from "lucide-react";

import { createReport } from "@/api/reports";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { ReportReason, ReportTargetType } from "@/types";

const REASON_LABELS: Record<ReportReason, string> = {
  spam: "Spam",
  inappropriate: "Inappropriate content",
  fraud: "Fraud or scam",
  other: "Other",
};

interface ReportModalProps {
  targetType: ReportTargetType;
  targetId: string;
  triggerLabel?: string;
}

export function ReportModal({ targetType, targetId, triggerLabel = "Report" }: ReportModalProps) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<ReportReason>("spam");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleOpen() {
    setSubmitted(false);
    setError(null);
    setDescription("");
    setReason("spam");
    setOpen(true);
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      await createReport(targetType, targetId, reason, description);
      setSubmitted(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not submit the report. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <button
        onClick={handleOpen}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-destructive"
      >
        <Flag className="h-3.5 w-3.5" />
        {triggerLabel}
      </button>

      <Dialog open={open} onClose={() => setOpen(false)} title={`Report ${targetType}`}>
        {submitted ? (
          <p className="text-sm text-muted-foreground">
            Thanks for letting us know. Our team will take a look.
          </p>
        ) : (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="reason">Reason</Label>
              <Select id="reason" value={reason} onChange={(e) => setReason(e.target.value as ReportReason)}>
                {Object.entries(REASON_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Details (optional)</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What happened?"
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button className="w-full" onClick={handleSubmit} disabled={submitting}>
              {submitting ? "Submitting..." : "Submit report"}
            </Button>
          </div>
        )}
      </Dialog>
    </>
  );
}
