import { useState } from "react";
import { Flag } from "lucide-react";
import { useTranslation } from "react-i18next";

import { createReport } from "@/api/reports";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { ReportReason, ReportTargetType } from "@/types";

const REASON_VALUES: ReportReason[] = ["spam", "inappropriate", "fraud", "other"];

interface ReportModalProps {
  targetType: ReportTargetType;
  targetId: string;
  triggerLabel?: string;
}

export function ReportModal({ targetType, targetId, triggerLabel }: ReportModalProps) {
  const { t } = useTranslation();
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
      setError(err?.response?.data?.detail || t("report.error"));
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
        {triggerLabel ?? t("report.trigger")}
      </button>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={targetType === "listing" ? t("report.titleListing") : t("report.titleUser")}
      >
        {submitted ? (
          <p className="text-sm text-muted-foreground">
            {t("report.thanks")}
          </p>
        ) : (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="reason">{t("report.reason")}</Label>
              <Select id="reason" value={reason} onChange={(e) => setReason(e.target.value as ReportReason)}>
                {REASON_VALUES.map((value) => (
                  <option key={value} value={value}>
                    {t(`reportReason.${value}`)}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">{t("report.details")}</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t("report.detailsPlaceholder")}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button className="w-full" onClick={handleSubmit} disabled={submitting}>
              {submitting ? t("report.submitting") : t("report.submit")}
            </Button>
          </div>
        )}
      </Dialog>
    </>
  );
}
