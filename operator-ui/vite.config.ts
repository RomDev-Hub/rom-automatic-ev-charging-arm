import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Core that the dev server proxies /api to, REST and WSS alike (REQ-HMI-012); listed in deploy/.env.example.
const coreUrl = process.env.EV_ARM_CORE_URL || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: coreUrl, ws: true },
    },
  },
  test: {
    environment: "jsdom",
    // Testing Library unmounts what a test rendered only when afterEach is global.
    globals: true,
    restoreMocks: true,
    unstubGlobals: true,
  },
});
