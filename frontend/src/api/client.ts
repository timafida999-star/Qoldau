import axios from "axios";

// API base. In production it is left unset so it defaults to "<base>api" (e.g.
// "/qoldau/api"), which is same-origin and follows whatever subpath the app is
// served under. In dev it is set explicitly (VITE_API_URL) to the backend origin.
export const API_BASE_URL =
  import.meta.env.VITE_API_URL || `${import.meta.env.BASE_URL}api`;

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
  // API_BASE_URL may be absolute ("http://localhost:8000/api") in dev or a
  // same-origin path ("/qoldau/api") in production. Build a ws/wss URL for both.
  if (/^https?:/i.test(API_BASE_URL)) {
    return `${API_BASE_URL.replace(/^http/i, "ws")}${path}`;
  }
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}${API_BASE_URL}${path}`;
}
