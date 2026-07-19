import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { fetchExchange } from "@/api/exchanges";
import { createReview } from "@/api/reviews";
import { getUser } from "@/api/users";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { StarRating } from "@/components/StarRating";
import { Textarea } from "@/components/ui/textarea";
import type { Exchange, PublicUser } from "@/types";

export default function LeaveReviewPage() {
  const { exchangeId } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [exchange, setExchange] = useState<Exchange | null>(null);
  const [reviewee, setReviewee] = useState<PublicUser | null>(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!exchangeId) return;
    fetchExchange(exchangeId)
      .then(async (ex) => {
        setExchange(ex);
        const revieweeId = ex.role === "owner" ? ex.requester_id : ex.owner_id;
        const person = await getUser(revieweeId);
        setReviewee(person);
      })
      .finally(() => setLoading(false));
  }, [exchangeId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!exchangeId || rating === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await createReview(exchangeId, rating, comment);
      setSubmitted(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || t("review.error"));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <div className="container py-16 text-center text-muted-foreground">{t("common.loading")}</div>;
  }

  if (!exchange || !reviewee) {
    return <div className="container py-16 text-center text-muted-foreground">{t("exchange.notFound")}</div>;
  }

  if (submitted) {
    return (
      <div className="container max-w-lg py-16 text-center">
        <CheckCircle2 className="mx-auto mb-4 h-12 w-12 text-primary" />
        <h1 className="text-2xl font-semibold">{t("review.thanksTitle")}</h1>
        <Button className="mt-6" onClick={() => navigate(`/profile/${reviewee.id}`)}>
          {t("review.viewProfile", { name: reviewee.full_name })}
        </Button>
      </div>
    );
  }

  return (
    <div className="container max-w-lg py-12">
      <Card>
        <CardHeader>
          <CardTitle>{t("review.title")}</CardTitle>
          <p className="text-sm text-muted-foreground">
            {t("review.subtitle", { listing: exchange.listing_title, name: reviewee.full_name })}
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label>{t("review.rating")}</Label>
              <StarRating value={rating} onChange={setRating} size={28} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="comment">{t("review.commentLabel")}</Label>
              <Textarea
                id="comment"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder={t("review.commentPlaceholder")}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={rating === 0 || submitting}>
              {submitting ? t("review.submitting") : t("review.submit")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
