import { expect, test } from "@playwright/test";
import { postLearnNext, submitReviewAnswer } from "./learning-api.js";
import { loginAsLearner } from "./helpers.js";

test.describe.configure({ mode: "serial" });

test.describe("learning flow", () => {
  test.beforeEach(({ page }) => {
    page.on("dialog", (d) => d.accept());
  });

  test(
    "first-time learn setup, study queue, then review with correct answer",
    async ({ page }) => {
      await test.step("Login", async () => {
        await loginAsLearner(page);
      });

      await test.step("Learn page and onboarding", async () => {
        await page.goto("/learn");
        // Substring match would also hit "Ready to learn!" — require exact title.
        await expect(page.getByRole("heading", { name: "Learn", exact: true })).toBeVisible();
        await expect(page.locator(".learn-page .loading")).toHaveCount(0, { timeout: 25_000 });
        await expect(page.locator(".onboarding, .active-learning").first()).toBeVisible({
          timeout: 5_000,
        });

        const onboarding = page.locator(".onboarding");
        if (await onboarding.isVisible()) {
          const firstLevel = page.locator(".level-card:not(.disabled)").first();
          await expect(firstLevel, "At least one level with prompts is required (run make seed)").toBeVisible({
            timeout: 15_000,
          });
          await firstLevel.click();
          await page.getByRole("button", { name: /Start Learning/i }).click();
          await page.waitForURL(/\/(learn|study)/, { timeout: 45_000 });
          if (/\/learn/.test(page.url())) {
            const studyLink = page.locator("a.study-btn");
            if (await studyLink.isVisible()) {
              await studyLink.click();
              await page.waitForURL("**/study", { timeout: 20_000 });
            } else {
              await page.goto("/study");
            }
          }
        } else {
          const studyBtn = page.getByRole("link", { name: /Start Studying/i });
          if (await studyBtn.isVisible()) {
            await studyBtn.click();
            await page.waitForURL("**/study", { timeout: 20_000 });
          } else {
            await page.goto("/study");
          }
        }

        await expect(page).toHaveURL(/\/study$/);
      });

      await test.step("Study queue ready", async () => {
        // Study.vue shows only loading-state until /api/learn/study-queue returns; do not
        // treat "empty" before then (otherwise we skip the skip and time out on .study-container).
        await expect(page.locator(".study-page .loading-state")).toHaveCount(0, { timeout: 25_000 });

        const emptyStudy = page.locator(".study-page .empty-state");
        if (await emptyStudy.isVisible()) {
          const refill = await postLearnNext(page, 10);
          if (!refill.ok || refill.addedLen === 0) {
            test.skip(
              true,
              `Study queue empty and learn/next could not add items (ok=${refill.ok} added=${refill.addedLen} http=${refill.status}). ` +
                "Reset learner progress or set PLAYWRIGHT_API_BASE_URL to match your API host."
            );
          }
          await page.goto("/study");
          await expect(page.locator(".study-page .loading-state")).toHaveCount(0, { timeout: 25_000 });
          if (await page.locator(".study-page .empty-state").isVisible()) {
            test.skip(true, "Study queue still empty after learn/next refill.");
          }
        }

        await expect(page.locator(".study-container")).toBeVisible({ timeout: 15_000 });
        await expect(page.locator(".content-card").first()).toBeVisible();
      });

      await test.step("Advance study to review", async () => {
        const primaryNav = page.locator(".nav-footer button.btn.primary.lg");
        let reachedReviewNav = false;
        for (let i = 0; i < 60; i++) {
          const text = (await primaryNav.textContent()) || "";
          if (/Start Review/i.test(text)) {
            await primaryNav.click();
            reachedReviewNav = true;
            break;
          }
          await primaryNav.click();
        }
        expect(reachedReviewNav, "Expected the last study card to offer Start Review").toBe(true);

        await expect(page).toHaveURL(/\/review$/, { timeout: 20_000 });
      });

      await test.step("Review wrong-then-correct", async () => {
        await expect(page.locator(".review-page .loading-state")).toHaveCount(0, { timeout: 25_000 });

        if (await page.getByRole("heading", { name: /All caught up/i }).isVisible()) {
          test.skip(true, "No review items due yet for this user (scheduling / clock).");
        }

        const answerInput = page.locator(".answer-input");
        const reviewCard = page.locator(".review-page .review-card[data-prompt-id]");
        await expect(answerInput).toBeVisible({ timeout: 20_000 });

        const solutions = new Map();

        let data = await submitReviewAnswer(page, "__playwright_wrong__");
        expect(data.correct, "First answer should be graded incorrect").toBe(false);
        expect(data.expected_answer, "API should return expected_answer when incorrect").toBeTruthy();

        let pid = await reviewCard.getAttribute("data-prompt-id");
        expect(pid, "review-card should expose data-prompt-id").toBeTruthy();
        solutions.set(pid, String(data.expected_answer).trim());

        // Wrong answers re-queue the item (Review.vue next()). Cache expected_answer per
        // prompt_id; when the same id appears again, submit the cached canonical answer.
        let sawCorrect = false;
        for (let i = 0; i < 200; i++) {
          await expect(page.locator(".result-card.incorrect")).toBeVisible({ timeout: 10_000 });
          await page.keyboard.press("Enter");
          await expect(answerInput).toBeVisible({ timeout: 10_000 });

          pid = await reviewCard.getAttribute("data-prompt-id");
          expect(pid).toBeTruthy();
          const guess = solutions.get(pid) ?? "__playwright_wrong__";
          data = await submitReviewAnswer(page, guess);

          if (data.correct) {
            sawCorrect = true;
            break;
          }
          expect(data.expected_answer, "Each incorrect grade should include expected_answer").toBeTruthy();
          solutions.set(pid, String(data.expected_answer).trim());
        }

        expect(sawCorrect, "Should submit a correct cloze answer after re-queued prompts").toBe(true);
        await expect(page.locator(".result-card.correct")).toBeVisible({ timeout: 15_000 });
      });
    },
    { timeout: 180_000 }
  );
});
