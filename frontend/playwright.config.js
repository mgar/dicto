import { defineConfig, devices } from "@playwright/test";

// Must match API_CORS_ORIGIN / VITE_* host in `.env` (see `.env.example`).
// Using `127.0.0.1` here while the API is `localhost` breaks CORS and cookie sessions.
const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:5173";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
