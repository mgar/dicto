<template>
  <div class="review-page">
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading reviews...</p>
    </div>

    <!-- Done / completion state -->
    <div v-else-if="done" class="done-state">
      <div class="done-icon">
        <Icon name="check-circle" stroke-width="1.5" />
      </div>
      <h2>Session complete!</h2>
      <div class="accuracy-display">
        <span class="accuracy-number">{{ accuracyPercent }}%</span>
        <span class="accuracy-label">accuracy</span>
      </div>
      <p class="session-summary muted">
        {{ firstAttemptCorrect }} of {{ sessionTotal }} correct on first try
        <template v-if="totalAttempts > sessionTotal">
          · {{ totalAttempts - sessionTotal }} {{ totalAttempts - sessionTotal === 1 ? 'retry' : 'retries' }} needed
        </template>
      </p>
      <div class="btn-row-center">
        <RouterLink class="btn" to="/dashboard">Back to Dashboard</RouterLink>
        <button class="btn secondary" @click="loadQueue">New Session</button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="queue.length === 0" class="empty-state">
      <div class="empty-icon">
        <Icon name="check-circle" stroke-width="1.5" />
      </div>
      <h2>All caught up!</h2>
      <p class="muted">No reviews due right now. Come back later or add more items to learn.</p>
      <div class="empty-actions">
        <RouterLink class="btn" to="/learn">Add More Items</RouterLink>
      </div>
    </div>

    <!-- Review card -->
    <div v-else class="review-container">
      <section class="review-stage">
        <!-- Progress indicator -->
        <div class="progress-shell">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <div class="progress-header">
            <div class="progress-text">{{ correctAttempts }} / {{ sessionTotal }}</div>
            <button class="end-session-btn ghost-btn" @click="showEndConfirm = true">
              End Session
            </button>
          </div>
        </div>

        <!-- End session confirmation modal -->
        <div v-if="showEndConfirm" class="modal-overlay" @click.self="showEndConfirm = false">
          <div class="modal-card surface">
            <h3>End session early?</h3>
            <p class="muted">
              You've completed {{ correctAttempts }} of {{ sessionTotal }} reviews.
              The remaining {{ sessionTotal - correctAttempts }} will stay in your queue.
            </p>
            <div class="btn-row-center">
              <button class="btn secondary" @click="showEndConfirm = false">Keep Going</button>
              <button class="btn danger" @click="endSession">End Session</button>
            </div>
          </div>
        </div>

        <div class="review-card surface" :data-prompt-id="current?.prompt_id">
          <!-- Type badge - don't reveal the answer! -->
          <TypeBadge :type="current.kind">
            {{ current.kind === 'grammar' ? current.grammar_title : 'Vocabulary' }}
          </TypeBadge>

          <!-- Sentence with live input -->
          <div class="sentence-container">
            <p class="sentence">
              <template v-for="(part, idx) in sentenceParts" :key="idx">
                <span v-if="part.type === 'text'">{{ part.content }}</span>
                <span
                  v-else
                  class="inline-input"
                  :class="{
                    typing: answer.length > 0,
                    correct: result?.correct,
                    incorrect: result && !result.correct
                  }"
                >
                  <span v-if="result" class="final-answer">
                    {{ result.correct && !resultNeedsRetry ? submittedAnswer : result.expected_answer }}
                  </span>
                  <span v-else-if="answer" class="live-input">{{ answer }}</span>
                  <span v-else class="placeholder">______</span>
                  <span v-if="!result && answer" class="cursor"></span>
                </span>
              </template>
            </p>
          </div>

          <!-- Primary instruction (always visible) -->
          <div class="instruction" v-if="current.notes">
            {{ current.notes }}
          </div>

          <!-- Additional hint (only when user clicks hint) -->
          <div class="context-hint" v-if="showHint >= 1">
            <div class="hint-icon">
              <Icon name="info" />
            </div>
            <div class="hint-text">
              <span v-if="current.kind === 'grammar'">
                {{ getGrammarHint() }}
              </span>
              <span v-else>
                {{ getVocabHint() }}
              </span>
            </div>
          </div>
        </div>

        <!-- Answer section -->
        <div class="answer-section">
          <!-- Result feedback -->
          <div v-if="result" class="result-card" :class="{ correct: result.correct, incorrect: !result.correct }">
            <div class="result-icon">
              <Icon v-if="result.correct" name="check" stroke-width="2.5" />
              <Icon v-else name="x" stroke-width="2.5" />
            </div>
            <div class="result-content">
              <div class="result-title">
                {{ resultNeedsRetry ? 'Accent needed' : result.correct ? 'Correct!' : 'Not quite' }}
                <span v-if="result.flags?.missing_accent" class="accent-note">(accent missing)</span>
              </div>
              <div v-if="!result.correct" class="expected-answer">
                Expected: <strong>{{ result.expected_answer }}</strong>
              </div>
              <div v-else-if="resultNeedsRetry" class="expected-answer">
                Correct spelling: <strong>{{ result.expected_answer }}</strong>
              </div>
              <div class="your-answer">
                Your answer: <span :class="{ wrong: !result.correct }">{{ submittedAnswer }}</span>
              </div>
            </div>
            <div class="result-actions">
              <button class="btn secondary lg info-scroll-btn" type="button" @click="scrollToInfo">
                <Icon name="info" />
                <span>Show Info</span>
              </button>
              <button class="btn lg next-btn" @click="next">
                <span>Continue</span>
                <Icon name="chevron-right" />
              </button>
            </div>
          </div>

          <!-- Input form -->
          <form v-else class="answer-form" @submit.prevent="submit">
            <div class="input-wrapper surface">
              <input
                ref="answerInput"
                class="answer-input"
                v-model="answer"
                :placeholder="getPlaceholder()"
                :disabled="submitting"
                autocomplete="off"
                autocapitalize="off"
                spellcheck="false"
              />
              <button type="submit" class="btn icon-only submit-btn" :disabled="submitting || !answer.trim()">
                <Icon name="send" />
              </button>
            </div>
          </form>
        </div>
      </section>

      <div ref="infoAnchorRef" class="info-anchor">
        <ReviewInfoPanel
          v-if="result && current"
          :item="current"
          :detail="currentInfoDetail"
          :loading="infoLoading"
          :error="infoError"
        />
        <div v-else class="info-placeholder" aria-hidden="true"></div>
      </div>

      <!-- Hint toggle -->
      <button class="hint-toggle ghost-btn" @click="toggleHint" :class="{ active: showHint > 0 }" title="Toggle hint (H)">
        <Icon name="lightbulb" class="lightbulb-icon" />
        <span class="hint-label">Hint</span>
      </button>

      <!-- Keyboard shortcut hint -->
      <div class="keyboard-hint">
        Press <kbd>Enter</kbd> to submit · <kbd>H</kbd> for hint
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { apiFetch, localDateString, timezonePayload } from "../api";
import { useCounts } from "../counts";
import TypeBadge from "../components/badges/TypeBadge.vue";
import Icon from "../components/Icon.vue";
import ReviewInfoPanel from "../components/review/ReviewInfoPanel.vue";

const counts = useCounts();
const queue = ref([]);
const loading = ref(false);
const submitting = ref(false);

const index = ref(0);
const answer = ref("");
const submittedAnswer = ref("");
const result = ref(null);
const showHint = ref(0);
const answerInput = ref(null);
const infoAnchorRef = ref(null);
const infoCache = ref({});
const infoLoading = ref(false);
const infoError = ref("");
let infoRequestId = 0;

const done = ref(false);
const showEndConfirm = ref(false);
const sessionTotal = ref(0);
const totalAttempts = ref(0);
const correctAttempts = ref(0);
const firstAttemptCorrect = ref(0);
let seenOnce = new Set();

const current = computed(() => queue.value[index.value]);
const currentInfoKey = computed(() => {
  if (!current.value) return "";
  if (current.value.kind === "grammar" && current.value.grammar_point_id) {
    return `grammar:${current.value.grammar_point_id}`;
  }
  if (current.value.kind === "vocab" && current.value.vocab_item_id) {
    return `vocab:${current.value.vocab_item_id}`;
  }
  return "";
});
const currentInfoDetail = computed(() => {
  if (!currentInfoKey.value) return null;
  return infoCache.value[currentInfoKey.value] || null;
});
const resultNeedsRetry = computed(() => Boolean(result.value?.flags?.missing_accent));
const progressPercent = computed(() => {
  if (sessionTotal.value === 0) return 0;
  return (correctAttempts.value / sessionTotal.value) * 100;
});
const accuracyPercent = computed(() => {
  if (totalAttempts.value === 0) return 0;
  return Math.round((correctAttempts.value / totalAttempts.value) * 100);
});

const sentenceParts = computed(() => {
  if (!current.value) return [];
  const sentence = current.value.sentence;
  const parts = [];
  const regex = /_{2,}/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(sentence)) !== null) {
    // Add text before the blank
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: sentence.slice(lastIndex, match.index) });
    }
    // Add the blank
    parts.push({ type: 'blank' });
    lastIndex = match.index + match[0].length;
  }

  // Add remaining text after last blank
  if (lastIndex < sentence.length) {
    parts.push({ type: 'text', content: sentence.slice(lastIndex) });
  }

  return parts;
});

function getPlaceholder() {
  if (!current.value) return "Type your answer...";
  return "Type the missing word...";
}

function getGrammarHint() {
  if (!current.value) return "";
  return `This exercise practices: ${current.value.grammar_title}`;
}

function getVocabHint() {
  if (!current.value) return "";
  
  const parts = [];
  
  // Part of speech with gender if applicable
  if (current.value.vocab_pos) {
    let posText = current.value.vocab_pos;
    if (current.value.vocab_gender) {
      posText += ` (${current.value.vocab_gender})`;
    }
    parts.push(posText);
  }
  
  // First letter hint (without revealing too much)
  if (current.value.vocab_word) {
    const firstLetter = current.value.vocab_word.charAt(0).toUpperCase();
    const wordLength = current.value.vocab_word.length;
    parts.push(`starts with "${firstLetter}", ${wordLength} letters`);
  }
  
  return parts.length > 0 
    ? parts.join(' · ') 
    : `Level: ${current.value.vocab_level || 'Unknown'}`;
}

function toggleHint() {
  showHint.value = (showHint.value + 1) % 4;
}

// Fetch additional info for the current item
function getInfoEndpoint(item) {
  if (!item) return "";
  if (item.kind === "grammar" && item.grammar_point_id) {
    return `/api/grammar-points/${item.grammar_point_id}`;
  }
  if (item.kind === "vocab" && item.vocab_item_id) {
    return `/api/vocab-items/${item.vocab_item_id}`;
  }
  return "";
}

async function loadCurrentInfo() {
  const item = current.value;
  const key = currentInfoKey.value;
  const endpoint = getInfoEndpoint(item);
  const requestId = ++infoRequestId;
  infoError.value = "";
  if (!key || !endpoint || infoCache.value[key]) {
    infoLoading.value = false;
    return;
  }

  infoLoading.value = true;
  try {
    const detail = await apiFetch(endpoint);
    if (requestId !== infoRequestId) return;
    infoCache.value = {
      ...infoCache.value,
      [key]: detail,
    };
  } catch {
    if (requestId !== infoRequestId) return;
    infoError.value = "Could not load this item's info.";
  } finally {
    if (requestId === infoRequestId) {
      infoLoading.value = false;
    }
  }
}

async function scrollToInfo() {
  if (!result.value) return;
  await loadCurrentInfo();
  await nextTick();
  infoAnchorRef.value?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}

async function loadQueue() {
  loading.value = true;
  result.value = null;
  answer.value = "";
  index.value = 0;
  showHint.value = 0;
  done.value = false;
  try {
    const data = await apiFetch("/api/reviews/queue?limit=20");
    queue.value = data.items;
    sessionTotal.value = data.items.length;
    totalAttempts.value = 0;
    correctAttempts.value = 0;
    firstAttemptCorrect.value = 0;
    seenOnce = new Set();
    await nextTick();
    answerInput.value?.focus();
  } finally {
    loading.value = false;
  }
}

async function submit() {
  if (!answer.value.trim() || submitting.value) return;
  submitting.value = true;
  submittedAnswer.value = answer.value;
  try {
    // Include local date and timezone data for timezone-aware scheduling
    // Use local date parts (not toISOString which returns UTC)
    const now = new Date();
    const data = await apiFetch(`/api/reviews/${current.value.prompt_id}/answer`, {
      method: "POST",
      body: JSON.stringify({
        user_answer: answer.value,
        local_date: localDateString(now),
        ...timezonePayload(now),
      })
    });
    const isFirstAttempt = !seenOnce.has(current.value.prompt_id);
    seenOnce.add(current.value.prompt_id);
    totalAttempts.value++;
    const countsAsComplete = data.correct && !data.flags?.missing_accent;
    if (countsAsComplete) {
      correctAttempts.value++;
      if (isFirstAttempt) firstAttemptCorrect.value++;
    }
    if (countsAsComplete && isFirstAttempt && counts.state.dueNow != null) {
      counts.state.dueNow = Math.max(0, counts.state.dueNow - 1);
    }
    result.value = data;
  } finally {
    submitting.value = false;
  }
}

async function next() {
  const shouldRetry = !result.value?.correct || resultNeedsRetry.value;
  result.value = null;
  answer.value = "";
  showHint.value = 0;

  if (shouldRetry) {
    // Re-queue this item at the end — must be answered correctly to finish
    queue.value.push({ ...queue.value[index.value] });
  }

  if (index.value < queue.value.length - 1) {
    index.value += 1;
    await nextTick();
    answerInput.value?.focus();
  } else {
    // All items answered correctly — session complete
    done.value = true;
    await counts.refresh();
  }
}

function endSession() {
  showEndConfirm.value = false;
  // Adjust sessionTotal to reflect only what was attempted
  sessionTotal.value = seenOnce.size;
  done.value = true;
  counts.refresh();
}

// Keyboard shortcuts
function handleKeydown(e) {
  // Escape closes end-session modal
  if (e.key === 'Escape' && showEndConfirm.value) {
    showEndConfirm.value = false;
    return;
  }
  // Press H for hint (when not typing)
  if (e.key === 'h' && document.activeElement !== answerInput.value) {
    toggleHint();
  }
  // Press Enter to continue after result
  if (e.key === 'Enter' && result.value) {
    next();
  }
}

onMounted(() => {
  loadQueue();
  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
});

// Watch for changes in the current prompt or result
watch(
  () => [current.value?.prompt_id, Boolean(result.value)],
  ([, hasResult]) => {
    infoError.value = "";
    if (hasResult) {
      loadCurrentInfo();
    } else {
      infoLoading.value = false;
      infoRequestId++;
    }
  }
);
</script>

<style scoped>
.review-page {
  min-height: calc(100svh - 120px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: 0 20px 24px;
}

/* Done / completion state */
.done-state {
  text-align: center;
  max-width: 400px;
}

.done-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  background: var(--success-glow);
  border: 1px solid var(--success-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.done-icon svg {
  width: 36px;
  height: 36px;
  color: var(--success);
}

.done-state h2 {
  margin: 0 0 20px 0;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.accuracy-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-bottom: 10px;
}

.accuracy-number {
  font-size: 60px;
  font-weight: 800;
  color: var(--success);
  line-height: 1;
  letter-spacing: -0.04em;
}

.accuracy-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
}

.session-summary {
  margin: 0 0 28px 0;
  font-size: 14px;
}

/* Empty state overrides */
.empty-state {
  max-width: 400px;
}

.empty-icon {
  background: var(--success-glow);
  border: 1px solid var(--success-border);
}

.empty-icon svg {
  color: var(--success);
}

/* Review container */
.review-container {
  width: 100%;
  max-width: 1240px;
  position: relative;
}

.review-stage {
  min-height: calc(100svh - 112px);
  display: grid;
  grid-template-rows: auto 1fr auto;
  align-content: stretch;
  gap: 18px;
  padding: 8px 0 24px;
}

.progress-shell {
  width: 100%;
}

/* Progress bar */
.progress-bar {
  height: 3px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: var(--review-progress-gradient);
  transition: width 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  border-radius: 2px;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0;
}

.progress-text {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.end-session-btn {
  padding: 5px 12px;
  border-radius: 7px;
  font-size: 12.5px;
}

.end-session-btn:hover {
  border-color: var(--error-border-strong);
  color: var(--error);
  background: var(--error-tint);
}

/* Confirmation modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--modal-overlay);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-card {
  border-radius: 18px;
  padding: 28px 32px;
  max-width: 380px;
  width: 90%;
  text-align: center;
  animation: slideUp 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: var(--shadow-lg);
}

.modal-card h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.modal-card p {
  margin: 0 0 24px 0;
  font-size: 14px;
}

/* Review card */
.review-card {
  align-self: center;
  border-radius: 20px;
  height: clamp(520px, 58svh, 780px);
  padding: clamp(36px, 6svh, 64px) 64px clamp(72px, 10svh, 120px);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* TypeBadge spacing override for review layout */
.review-card :deep(.type-badge) {
  margin-bottom: 24px;
}

.sentence-container {
  margin-bottom: 20px;
}

.sentence {
  font-size: 36px;
  line-height: 1.65;
  margin: 0;
  font-weight: 600;
  letter-spacing: 0;
}

.inline-input {
  display: inline-block;
  min-width: 100px;
  padding: 4px 10px;
  margin: 0 5px;
  border-bottom: 2px solid var(--border-color);
  text-align: center;
  position: relative;
  transition: all 0.2s ease;
  border-radius: 4px 4px 0 0;
}

.inline-input.typing {
  border-bottom-color: var(--accent);
}

.inline-input.correct {
  border-bottom-color: var(--success);
  background: var(--success-glow);
  border-radius: 6px;
  border-bottom-width: 2px;
}

.inline-input.incorrect {
  border-bottom-color: var(--success);
  background: var(--success-glow);
  border-radius: 6px;
  border-bottom-width: 2px;
}

.inline-input .placeholder {
  color: var(--text-muted);
  opacity: 0.4;
}

.inline-input .live-input {
  color: var(--accent-light);
  font-weight: 600;
}

.inline-input .final-answer {
  color: var(--success);
  font-weight: 700;
}

.inline-input .cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--accent);
  margin-left: 1px;
  vertical-align: text-bottom;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.instruction {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 16px;
  padding: 10px 16px;
  background: var(--bg-tertiary);
  border-radius: 9px;
  border-left: 2px solid var(--accent);
}

.context-hint {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  border: 1px solid var(--border-color);
  font-size: 13.5px;
  color: var(--text-muted);
  margin-top: 14px;
  text-align: left;
  animation: slideUp 0.2s ease;
}

.hint-icon {
  flex-shrink: 0;
}

.hint-icon svg {
  width: 16px;
  height: 16px;
  color: var(--accent-light);
}

.hint-text {
  line-height: 1.55;
}

.info-scroll-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 14px;
  border-radius: 11px;
  font-size: 13.5px;
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.info-scroll-btn svg {
  width: 16px;
  height: 16px;
}

.info-scroll-btn:hover {
  border-color: var(--accent-border);
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}

.info-anchor {
  scroll-margin-top: 24px;
}

.info-placeholder {
  min-height: 1px;
}

/* Answer section */
.answer-section {
  width: min(100%, 560px);
  justify-self: center;
  margin-top: 0;
  margin-bottom: clamp(28px, 4svh, 56px);
  align-self: end;
}

.answer-form {
  width: 100%;
}

.input-wrapper {
  display: flex;
  align-items: center;
  border-radius: 14px;
  padding: 4px;
  transition: border-color 0.18s;
}

.input-wrapper:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.answer-input {
  flex: 1;
  background: var(--transparent);
  border: none;
  color: var(--text-primary);
  font-size: 16px;
  padding: 11px 16px;
  outline: none;
  font-family: inherit;
  font-weight: 500;
  letter-spacing: -0.01em;
}

.answer-input::placeholder {
  color: var(--text-muted);
  font-weight: 400;
}

.submit-btn {
  border-radius: 10px;
}

.submit-btn:hover:not(:disabled) {
  box-shadow: 0 4px 12px var(--accent-glow);
}

.submit-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Result card */
.result-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border-radius: 14px;
  animation: slideUp 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: var(--shadow-sm);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-card.correct {
  background: var(--success-surface);
  border: 1px solid var(--success-border);
}

.result-card.incorrect {
  background: var(--error-tint);
  border: 1px solid var(--error-border);
}

.result-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.result-card.correct .result-icon {
  background: var(--success-glow);
  color: var(--success);
}

.result-card.incorrect .result-icon {
  background: var(--error-tint-strong);
  color: var(--error);
}

.result-icon svg {
  width: 22px;
  height: 22px;
}

.result-content {
  flex: 1;
  text-align: left;
}

.result-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 3px;
  letter-spacing: -0.02em;
}

.result-card.correct .result-title {
  color: var(--success);
}

.result-card.incorrect .result-title {
  color: var(--error);
}

.accent-note {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-muted);
}

.expected-answer {
  font-size: 13.5px;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.expected-answer strong {
  color: var(--success);
  font-weight: 700;
}

.your-answer {
  font-size: 12.5px;
  color: var(--text-muted);
}

.your-answer .wrong {
  color: var(--error);
  text-decoration: line-through;
}

.result-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.next-btn {
  display: inline-flex;
  gap: 5px;
  border-radius: 11px;
}

/* Hint toggle */
.hint-toggle {
  position: fixed;
  bottom: 24px;
  left: 24px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 14px;
  border-radius: 11px;
  font-size: 13.5px;
  font-weight: 500;
  box-shadow: var(--shadow-sm);
}

.hint-toggle:hover {
  border-color: var(--warning-border);
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}

.hint-toggle.active {
  border-color: var(--warning-border-strong);
  color: var(--warning);
  background: var(--warning-surface);
}

.lightbulb-icon {
  width: 18px;
  height: 18px;
  transition: all 0.18s ease;
}

.hint-toggle.active .lightbulb-icon {
  fill: var(--warning-fill);
  filter: drop-shadow(0 0 4px var(--warning-glow));
}

.hint-label {
  display: none;
}

@media (min-width: 480px) {
  .hint-label {
    display: inline;
  }
}

/* Keyboard hint */
.keyboard-hint {
  position: fixed;
  bottom: 20px;
  right: 24px;
  font-size: 12px;
  color: var(--text-muted);
  opacity: 0.5;
}

/* Responsive */
@media (max-width: 640px) {
  .review-page {
    padding-inline: 0;
  }

  .review-stage {
    min-height: calc(100svh - 96px);
    grid-template-rows: auto 1fr auto;
    padding: 12px 0 24px;
  }

  .review-card {
    height: clamp(380px, 56svh, 520px);
    padding: 32px 20px 56px;
  }

  .sentence {
    font-size: 24px;
  }

  .answer-section {
    margin-bottom: 16px;
  }

  .hint-toggle,
  .keyboard-hint {
    position: static;
    margin-top: 20px;
  }

  .keyboard-hint {
    text-align: center;
    opacity: 0.5;
  }

  .result-card {
    flex-direction: column;
    text-align: center;
  }

  .result-content {
    text-align: center;
  }

  .result-actions {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>
