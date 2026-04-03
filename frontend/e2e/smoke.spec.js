import { expect, test } from "@playwright/test";
import { loginAsLearner } from "./helpers.js";

test.describe("smoke", () => {
  test("home offers login", async ({ page }) => {
    await page.goto("/");
    // Hero CTA (nav also has "Get Started"; getByRole name match is case-insensitive).
    const heroCta = page.locator(".hero .hero-btn");
    await expect(heroCta).toBeVisible();
    await expect(heroCta).toHaveText(/get started/i);
  });

  test("login with default user reaches dashboard", async ({ page }) => {
    await loginAsLearner(page);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });
});
