export const TEST_LEARNER = {
  email: process.env.E2E_USER_EMAIL || "test@dicto.es",
  password: process.env.E2E_USER_PASSWORD || "uoc123456",
};

/**
 * Logs in the default learner and waits for the dashboard.
 */
export async function loginAsLearner(page) {
  await page.goto("/login");
  await page.locator('input[type="email"]').fill(TEST_LEARNER.email);
  await page.locator('input[type="password"]').fill(TEST_LEARNER.password);
  await page.locator("form button.login-submit").click();
  await page.waitForURL("**/dashboard", { timeout: 30_000 });
}
