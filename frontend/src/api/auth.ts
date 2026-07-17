import { apiClient } from "./client";
import type { LoginInput, RegisterInput, TokenResponse, User } from "@/types";

export async function register(payload: RegisterInput): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/register", payload);
  return data;
}

export async function login(payload: LoginInput): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}
