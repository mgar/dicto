import { defineConfig, devices } from "@playwright/test";

// Must match API_CORS_ORIGIN / VITE_* host in `.env` (see `.env.example`).
// Using `127.0.0.1` here while the API is `localhost` breaks CORS and cookie sessions.
const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:5173";

export default defineConfig({
  testDir: "./e2e",
  // All specs share the default API user; parallel workers cause flaky learn/review state.
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.E2E_WORKERS ? parseInt(process.env.E2E_WORKERS, 10) : 1,
  reporter: "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});