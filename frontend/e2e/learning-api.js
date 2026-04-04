import { request } from "@playwright/test";

/** Match VITE_API_BASE_URL / docker `.env` so session cookies apply to this host. */
export function apiBaseUrl() {
  return (
    process.env.PLAYWRIGHT_API_BASE_URL ||
    process.env.VITE_API_BASE_URL ||
    "http://localhost:8000"
  );
}

/**
 * Pull new prompts into the study queue (status=learning) for the logged-in user.
 * Uses the same session as `page` (no CORS issues).
 */
export async function postLearnNext(page, count = 10) {
  const baseURL = apiBaseUrl();
  const ctx = await request.newContext({
    baseURL,
    storageState: await page.context().storageState(),
  });
  try {
    const res = await ctx.post(`/api/learn/next?count=${count}`);
    const ok = res.ok();
    let addedLen = 0;
    if (ok) {
      const body = await res.json();
      addedLen = Array.isArray(body.added) ? body.added.length : 0;
    }
    return { ok, status: res.status(), addedLen };
  } finally {
    await ctx.dispose();
  }
}

/**
 * Submit the review cloze form and return the JSON body from POST /api/reviews/:id/answer.
 * Uses the network response so expected_answer matches the server exactly (DOM text can differ).
 */
export async function submitReviewAnswer(page, text) {
  const answerInput = page.locator(".answer-input");
  const submitBtn = page.locator("form.answer-form button[type=submit]");
  await answerInput.fill(text);
  const responsePromise = page.waitForResponse(
    (r) => {
      if (r.request().method() !== "POST") return false;
      const u = r.url();
      return u.includes("/api/reviews/") && /\/reviews\/\d+\/answer(\?|$)/.test(u);
    },
    { timeout: 30_000 }
  );
  await submitBtn.click({ force: true });
  const response = await responsePromise;
  if (!response.ok()) {
    const body = await response.text().catch(() => "");
    throw new Error(`review answer HTTP ${response.status()}: ${body}`);
  }
  return response.json();
}
