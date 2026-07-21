import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("qoldau_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function getAuthToken(): string | null {
  return localStorage.getItem("qoldau_token");
}

export function wsUrl(path: string): string {
  const base = API_BASE_URL.replace(/^http/, "ws");
  return `${base}${path}`;
}
