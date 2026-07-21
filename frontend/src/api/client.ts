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

// Log rate-limit responses so throttling is visible in the console during
// development, then let the calling component handle the error as usual.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 429) {
      const retryAfter = error.response.headers?.["retry-after"];
      const url = error.config?.url ?? "unknown endpoint";
      console.warn(
        `[rate-limit] 429 from ${url}${retryAfter ? ` — retry after ${retryAfter}s` : ""}`
      );
    }
    return Promise.reject(error);
  }
);

export function getAuthToken(): string | null {
  return localStorage.getItem("qoldau_token");
}

export function wsUrl(path: string): string {
  const base = API_BASE_URL.replace(/^http/, "ws");
  return `${base}${path}`;
}
