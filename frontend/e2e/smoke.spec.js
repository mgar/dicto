import { expect, test } from "@playwright/test";

test.describe("smoke", () => {
  test("home offers login", async ({ page }) => {
    await page.goto("/");
    // Hero CTA (nav also has "Get Started"; getByRole name match is case-insensitive).
    const heroCta = page.locator(".hero .hero-btn");
    await expect(heroCta).toBeVisible();
    await expect(heroCta).toHaveText(/get started/i);
  });

  test("login with default user reaches dashboard", async ({ page }) => {
    await page.goto("/login");
    await page.locator('input[type="email"]').fill("test@dicto.es");
    await page.locator('input[type="password"]').fill("changeme");
    await page.locator("form button.login-submit").click();
    await page.waitForURL("**/dashboard", { timeout: 30_000 });
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });
});
