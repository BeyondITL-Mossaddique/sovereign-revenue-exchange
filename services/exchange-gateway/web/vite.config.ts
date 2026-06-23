import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Use a relative base so the built bundle works regardless of the mount
// prefix it is served under. The dashboard is served from the FastAPI app at
// "/" locally and under "/exchange-gateway-http/" through the OpenChoreo
// gateway — both work because every asset path resolves against the page's
// own URL.
export default defineConfig({
  base: "./",
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/exchange": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
