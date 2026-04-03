import { reactive } from "vue";
import { apiFetch } from "./api";

const state = reactive({
  dueNow: null,
  learnRemaining: null
});

export function useCounts() {
  async function refresh() {
    try {
      const [review, learn] = await Promise.all([
        apiFetch("/api/reviews/count"),
        apiFetch("/api/learn/count")
      ]);
      state.dueNow = review.due_now;
      state.learnRemaining = learn.remaining;
    } catch (e) {
      // If user is logged out or API errors, just clear counts
      state.dueNow = null;
      state.learnRemaining = null;
    }
  }

  return { state, refresh };
}
