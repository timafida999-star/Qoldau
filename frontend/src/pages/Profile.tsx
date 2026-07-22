import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useParams } from "react-router-dom";
import { Star, Upload } from "lucide-react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

import { API_BASE_URL } from "@/api/client";
import { getUser, updateMe, uploadAvatar } from "@/api/users";
import { fetchUserReviews } from "@/api/reviews";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ListingGrid } from "@/components/ListingGrid";
import { ReportModal } from "@/components/ReportModal";
import { StarRating } from "@/components/StarRating";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/useAuth";
import type { PublicUser, Review } from "@/types";

type ProfileForm = { full_name: string; phone?: string; bio?: string };

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", year: "numeric" });
}

export default function ProfilePage() {
  const { userId } = useParams();
  const { user: viewer, refreshUser } = useAuth();
  const { t } = useTranslation();
  const isOwnProfile = Boolean(viewer && viewer.id === userId);

  const profileSchema = z.object({
    full_name: z.string().min(2, t("profile.enterFullName")),
    phone: z.string().optional(),
    bio: z.string().optional(),
  });

  const [profile, setProfile] = useState<PublicUser | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [tab, setTab] = useState<"listings" | "given" | "reviews">("listings");
  const [loading, setLoading] = useState(true);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProfileForm>({ resolver: zodResolver(profileSchema) });

  async function load() {
    if (!userId) return;
    setLoading(true);
    try {
      const [person, personReviews] = await Promise.all([getUser(userId), fetchUserReviews(userId)]);
      setProfile(person);
      setReviews(personReviews);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  useEffect(() => {
    if (isOwnProfile && viewer) {
      reset({ full_name: viewer.full_name, phone: viewer.phone ?? "", bio: viewer.bio ?? "" });
    }
  }, [isOwnProfile, viewer, reset]);

  async function onSubmit(values: ProfileForm) {
    setSaveMessage(null);
    await updateMe(values);
    await refreshUser();
    await load();
    setSaveMessage(t("profile.updated"));
  }

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setAvatarUploading(true);
    try {
      await uploadAvatar(file);
      await refreshUser();
      await load();
    } finally {
      setAvatarUploading(false);
    }
  }

  if (loading) {
    return <div className="container py-16 text-center text-muted-foreground">{t("common.loading")}</div>;
  }

  if (!profile) {
    return <div className="container py-16 text-center text-muted-foreground">{t("profile.notFound")}</div>;
  }

  const avatarSrc = profile.avatar_url ? `${API_BASE_URL}${profile.avatar_url}` : undefined;

  return (
    <div className="container max-w-3xl py-12">
      <div className="mb-8 flex items-center gap-6">
        <div className="relative h-24 w-24 overflow-hidden rounded-full bg-secondary shadow-soft">
          {avatarSrc ? (
            <img src={avatarSrc} alt={profile.full_name} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-2xl font-semibold text-muted-foreground">
              {profile.full_name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        <div>
          <h1 className="text-2xl font-semibold">{profile.full_name}</h1>
          <div className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            {profile.rating_avg.toFixed(1)} ({profile.rating_count} {t("profile.reviewsSuffix")})
          </div>
          {profile.bio && <p className="mt-2 max-w-md text-sm text-foreground/80">{profile.bio}</p>}
          {isOwnProfile && (
            <label className="mt-3 inline-flex cursor-pointer items-center gap-2 text-sm font-medium text-primary hover:underline">
              <Upload className="h-4 w-4" />
              {avatarUploading ? t("profile.uploading") : t("profile.changePhoto")}
              <input type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
            </label>
          )}
          {!isOwnProfile && viewer && (
            <div className="mt-3">
              <ReportModal targetType="user" targetId={profile.id} triggerLabel={t("profile.reportUser")} />
            </div>
          )}
        </div>
      </div>

      {isOwnProfile && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>{t("profile.editProfile")}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="full_name">{t("profile.fullName")}</Label>
                <Input id="full_name" {...register("full_name")} />
                {errors.full_name && <p className="text-sm text-destructive">{errors.full_name.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">{t("profile.phone")}</Label>
                <Input id="phone" placeholder={t("profile.phonePlaceholder")} {...register("phone")} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bio">{t("profile.bio")}</Label>
                <Textarea id="bio" placeholder={t("profile.bioPlaceholder")} {...register("bio")} />
              </div>
              {saveMessage && <p className="text-sm text-primary">{saveMessage}</p>}
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? t("common.saving") : t("common.saveChanges")}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div>
        <div className="mb-6 flex gap-2 border-b border-border">
          {(["listings", "given", "reviews"] as const).map((key) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                tab === key
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {key === "reviews"
                ? t("profile.tabs.reviews", { count: reviews.length })
                : t(`profile.tabs.${key}`)}
            </button>
          ))}
        </div>

        {tab === "listings" && (
          <ListingGrid
            filters={{ owner: profile.id, status: "available" }}
            emptyText={t("profile.noListings")}
          />
        )}

        {tab === "given" && (
          <ListingGrid
            filters={{ owner: profile.id, status: "completed" }}
            emptyText={t("profile.noGiven")}
          />
        )}

        {tab === "reviews" &&
          (reviews.length === 0 ? (
            <p className="rounded-xl border border-dashed border-border p-8 text-center text-muted-foreground">
              {t("profile.noReviews")}
            </p>
          ) : (
            <div className="space-y-3">
              {reviews.map((review) => (
                <Card key={review.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{review.reviewer.full_name}</span>
                      <span className="text-xs text-muted-foreground">{formatDate(review.created_at)}</span>
                    </div>
                    <StarRating value={review.rating} readOnly size={16} />
                    {review.comment && <p className="mt-2 text-sm text-foreground/80">{review.comment}</p>}
                  </CardContent>
                </Card>
              ))}
            </div>
          ))}
      </div>
    </div>
  );
}
