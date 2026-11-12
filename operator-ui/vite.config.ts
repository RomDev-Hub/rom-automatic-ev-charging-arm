import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    // Testing Library unmounts what a test rendered only when afterEach is global.
    globals: true,
    restoreMocks: true,
    unstubGlobals: true,
  },
});
