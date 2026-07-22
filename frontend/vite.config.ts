import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  // Base public path. Defaults to "/" for local dev; the production build sets
  // VITE_BASE_PATH (e.g. "/qoldau/") so assets, router, and API URL all follow
  // the subpath the Public Nginx serves the app under.
  base: process.env.VITE_BASE_PATH || "/",
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
  },
});
