import { apiClient } from "./client";
import type { PublicUser, UserUpdateInput } from "@/types";

export async function getUser(userId: string): Promise<PublicUser> {
  const { data } = await apiClient.get<PublicUser>(`/users/${userId}`);
  return data;
}

export async function updateMe(payload: UserUpdateInput) {
  const { data } = await apiClient.patch("/users/me", payload);
  return data;
}

export async function uploadAvatar(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post("/users/me/avatar", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
