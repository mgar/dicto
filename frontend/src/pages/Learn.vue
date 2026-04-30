<template>
  <div class="learn-page">
    <!-- Header -->
    <div class="header">
      <div>
        <h2>Learn</h2>
        <p class="muted">Build your learning queue and start studying</p>
      </div>
      <div v-if="totalInQueue > 0" class="header-stats">
        <span class="pill">{{ totalInQueue }} items in queue</span>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <template v-else>
      <div
        v-if="feedback.text"
        class="feedback-banner"
        :class="feedback.type"
        :role="feedback.type === 'error' ? 'alert' : 'status'"
      >
        <span>{{ feedback.text }}</span>
        <button class="feedback-dismiss" type="button" aria-label="Dismiss message" @click="clearFeedback">
          <Icon name="x" />
        </button>
      </div>

      <!-- Empty State - Onboarding -->
      <div v-if="totalInQueue === 0" class="onboarding">
        <div class="welcome-card card">
          <div class="welcome-icon">
            <Icon name="book" stroke-width="1.5" />
          </div>
          <h3>Welcome to your learning journey!</h3>
          <p class="muted">Select the levels you want to learn. We'll add a daily batch and keep the rest for future days.</p>
        </div>

        <!-- Level Selection -->
        <div class="levels-section">
          <h4>Choose your levels</h4>
          <div class="levels-grid">
            <div 
              v-for="lvl in levels" 
              :key="lvl.level" 
              class="level-card"
              :class="{ selected: selectedLevels.includes(lvl.level), disabled: lvl.total_prompts === 0 }"
              @click="toggleLevel(lvl.level, lvl.total_prompts)"
            >
              <div class="level-header">
                <LevelBadge :level="lvl.level" />
                <div class="level-check" v-if="selectedLevels.includes(lvl.level)">
                  <Icon name="check" stroke-width="3" />
                </div>
              </div>
              <h5>{{ getLevelName(lvl.level) }}</h5>
              <div class="level-stats">
                <span>{{ lvl.grammar_points }} grammar</span>
                <span>{{ lvl.vocab_items }} vocab</span>
              </div>
              <div class="level-prompts">
                {{ lvl.total_prompts }} exercises
              </div>
            </div>
          </div>
        </div>

        <!-- Content type selection -->
        <div v-if="selectedLevels.length > 0" class="settings-section card">
          <h4>Content type</h4>
          <p class="muted">What do you want to learn?</p>
          
          <div class="daily-limit-options">
            <button 
              class="limit-option"
              :class="{ active: selectedContentKind === null }"
              @click="selectedContentKind = null"
            >
              <Icon name="book-open" class="limit-icon" />
              <span class="limit-label">Both</span>
            </button>
            <button 
              class="limit-option"
              :class="{ active: selectedContentKind === 'grammar' }"
              @click="selectedContentKind = 'grammar'"
            >
              <Icon name="bookmark" class="limit-icon" />
              <span class="limit-label">Grammar</span>
            </button>
            <button 
              class="limit-option"
              :class="{ active: selectedContentKind === 'vocab' }"
              @click="selectedContentKind = 'vocab'"
            >
              <Icon name="chat" class="limit-icon" />
              <span class="limit-label">Vocabulary</span>
            </button>
          </div>
        </div>

        <!-- Daily limit setting -->
        <div v-if="selectedLevels.length > 0" class="settings-section card">
          <h4>Daily learning goal</h4>
          <p class="muted">How many new items do you want to learn each day?</p>
          
          <div class="daily-limit-options">
            <button 
              v-for="option in dailyOptions" 
              :key="option.value"
              class="limit-option"
              :class="{ active: dailyLimit === option.value }"
              @click="dailyLimit = option.value"
            >
              <span class="limit-value">{{ option.value }}</span>
              <span class="limit-label">{{ option.label }}</span>
            </button>
          </div>
          <label class="custom-limit">
            <span>Custom daily maximum</span>
            <input class="input" type="number" v-model.number="dailyLimit" min="1" max="50" />
          </label>
        </div>

        <!-- Summary and Start -->
        <div v-if="selectedLevels.length > 0" class="start-section">
          <div class="summary-card card">
            <div class="summary-row">
              <span>Selected levels</span>
              <span class="summary-value">{{ selectedLevels.join(', ') }}</span>
            </div>
            <div class="summary-row">
              <span>Total exercises</span>
              <span class="summary-value">{{ totalSelectedPrompts }}</span>
            </div>
            <div class="summary-row">
              <span>Daily goal</span>
              <span class="summary-value">{{ normalizedDailyLimit }} items/day</span>
            </div>
            <div class="summary-row highlight">
              <span>Estimated completion</span>
              <span class="summary-value">~{{ Math.ceil(totalSelectedPrompts / normalizedDailyLimit) }} days</span>
            </div>
          </div>

          <button class="btn lg start-btn" @click="startLearning" :disabled="adding">
            <Icon v-if="!adding" name="play" />
            {{ adding ? 'Adding items...' : 'Start Learning' }}
          </button>
        </div>
      </div>

      <!-- Has items - Regular Learning View -->
      <div v-else class="active-learning">
        <!-- Primary action: Study new items -->
        <div v-if="newInQueue > 0" class="study-prompt">
          <div class="study-prompt-content">
            <div class="study-icon">
              <Icon name="book" />
            </div>
            <div class="study-text">
              <h3>Ready to learn!</h3>
              <p>You have <strong>{{ newInQueue }} new items</strong> waiting to be studied</p>
            </div>
          </div>
          <RouterLink class="btn lg study-btn" to="/study">
            Start Studying
            <Icon name="chevron-right" />
          </RouterLink>
        </div>

        <!-- Secondary: Stats and review -->
        <div class="stats-bar">
          <div class="stat stat-card">
            <span class="stat-value">{{ newInQueue }}</span>
            <span class="stat-label">New to study</span>
          </div>
          <div class="stat stat-card">
            <span class="stat-value">{{ dueNow }}</span>
            <span class="stat-label">Due for review</span>
          </div>
          <div class="stat stat-card clickable" @click="router.push('/review')" v-if="dueNow > 0">
            <span class="stat-action">Start Review →</span>
          </div>
        </div>

        <div class="daily-settings card">
          <div class="section-header-row">
            <div>
              <h3>Daily new items</h3>
              <p class="muted">Choose a daily pace that keeps new lessons fresh without piling up.</p>
            </div>
            <span class="pill subtle">{{ normalizedDailyLimit }} / day</span>
          </div>

          <div class="daily-settings-controls">
            <div class="segmented daily-limit-segments" aria-label="Daily new item presets">
              <button
                v-for="option in dailyOptions"
                :key="option.value"
                class="segment-btn"
                :class="{ active: dailyLimit === option.value }"
                @click="dailyLimit = option.value"
              >
                {{ option.value }}
              </button>
            </div>

            <label class="custom-limit inline">
              <span>Custom</span>
              <input class="input" type="number" v-model.number="dailyLimit" min="1" max="50" />
            </label>

            <button class="btn secondary" @click="saveLearningPreferences" :disabled="savingPreferences">
              {{ savingPreferences ? "Saving..." : "Save" }}
            </button>
          </div>
        </div>

        <!-- Expandable: Add more items -->
        <details class="add-more-section">
          <summary class="add-more-toggle">
            <span>Study more today</span>
            <span class="pill subtle">{{ availableToAdd }} available</span>
          </summary>
          
          <div class="add-more-content surface">
            <div class="add-controls">
              <div class="count-control">
                <label>Extra items</label>
                <div class="stepper">
                  <button class="stepper-btn" @click="count = Math.max(1, count - 1)">−</button>
                  <input class="stepper-input" type="number" v-model.number="count" min="1" max="50" />
                  <button class="stepper-btn" @click="count = Math.min(50, count + 1)">+</button>
                </div>
              </div>
              
              <div class="type-filter">
                <label>Type</label>
                <div class="segmented">
                  <button 
                    class="segment-btn" 
                    :class="{ active: selectedKind === null }"
                    @click="selectedKind = null"
                  >All</button>
                  <button 
                    class="segment-btn" 
                    :class="{ active: selectedKind === 'grammar' }"
                    @click="selectedKind = 'grammar'"
                  >Grammar</button>
                  <button 
                    class="segment-btn" 
                    :class="{ active: selectedKind === 'vocab' }"
                    @click="selectedKind = 'vocab'"
                  >Vocab</button>
                </div>
              </div>

              <button class="btn" @click="learnNext" :disabled="learning || availableToAdd === 0">
                <Icon v-if="!learning" name="plus" />
                {{ learning ? "Adding..." : `Add ${count} More` }}
              </button>
            </div>
          </div>
        </details>

        <!-- Recently added -->
        <div v-if="added.length > 0" class="recently-added card">
          <div class="section-header-row">
            <h3>Just Added</h3>
            <span class="pill">{{ added.length }} items</span>
          </div>
          <div class="items-list">
            <div v-for="item in added" :key="item.prompt_id" class="item">
              <span class="item-type" :class="item.kind">{{ item.kind }}</span>
              <span class="item-title">{{ item.grammar_title || item.vocab_word }}</span>
              <span class="item-sentence">{{ item.sentence }}</span>
            </div>
          </div>
        </div>

        <!-- Unlock levels -->
        <div class="unlock-levels card">
          <h3>Unlock new levels</h3>
          <p class="muted">Unlocked levels feed your daily batches without increasing today's queue beyond your limit.</p>
          
          <div class="mini-levels">
            <div 
              v-for="lvl in levels" 
              :key="lvl.level" 
              class="mini-level"
              :class="{ complete: lvl.fully_added, unlocked: isLevelUnlocked(lvl.level) }"
            >
              <div class="mini-level-info">
                <LevelBadge :level="lvl.level" size="small" />
                <span class="mini-level-name">{{ getLevelName(lvl.level) }}</span>
              </div>
              <div class="mini-level-progress">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: getProgress(lvl) + '%' }"></div>
                </div>
                <span class="progress-text">{{ lvl.in_queue }}/{{ lvl.total_prompts }}</span>
              </div>
              <button 
                class="btn secondary small" 
                :class="{ 'remove-level-btn': isLevelUnlocked(lvl.level) }"
                @click="toggleWholeLevel(lvl)"
                :disabled="isLevelActionDisabled(lvl)"
              >
                {{ levelActionLabel(lvl) }}
              </button>
            </div>
          </div>
          
          <div class="inline-links">
            <RouterLink to="/grammar">Browse grammar points →</RouterLink>
            <RouterLink to="/vocab">Browse vocabulary →</RouterLink>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { apiFetch, timezoneQuery } from "../api";
import { useCounts } from "../counts";
import LevelBadge from "../components/badges/LevelBadge.vue";
import Icon from "../components/Icon.vue";

const router = useRouter();
const counts = useCounts();

// Loading states
const loading = ref(true);
const adding = ref(false);
const learning = ref(false);
const addingLevelName = ref(null);
const removingLevelName = ref(null);
const savingPreferences = ref(false);
const feedback = reactive({
  type: "info",
  text: "",
});

// Level data
const levels = ref([]);
const totalInQueue = ref(0);

// Onboarding selections
const selectedLevels = ref([]);
const dailyLimit = ref(10);
const selectedContentKind = ref(null); // null = both, 'grammar' or 'vocab'

// Active learning
const availableToAdd = ref(0);
const newInQueue = ref(0);
const added = ref([]);
const count = ref(1);
const selectedKind = ref(null);

const dueNow = computed(() => counts.state.dueNow || 0);
const normalizedDailyLimit = computed(() => {
  const parsed = Number(dailyLimit.value);
  if (!Number.isFinite(parsed)) return 1;
  return Math.min(50, Math.max(1, Math.round(parsed)));
});

const dailyOptions = [
  { value: 5, label: 'Relaxed' },
  { value: 10, label: 'Moderate' },
  { value: 20, label: 'Intensive' },
  { value: 30, label: 'Challenge' },
];

const levelNames = {
  A1: "Beginner",
  A2: "Elementary", 
  B1: "Intermediate",
  B2: "Upper Intermediate",
  C1: "Advanced",
  C2: "Mastery",
};

function getLevelName(level) {
  return levelNames[level] || level;
}

function getProgress(lvl) {
  if (lvl.total_prompts === 0) return 0;
  return Math.round((lvl.in_queue / lvl.total_prompts) * 100);
}

function isLevelUnlocked(level) {
  return selectedLevels.value.includes(level);
}

function levelActionLabel(lvl) {
  if (addingLevelName.value === lvl.level || removingLevelName.value === lvl.level) return "...";
  if (isLevelUnlocked(lvl.level)) return "Remove";
  if (lvl.fully_added) return "Done";
  return "Add";
}

function isLevelActionDisabled(lvl) {
  return Boolean(
    addingLevelName.value === lvl.level
      || removingLevelName.value === lvl.level
      || (lvl.fully_added && !isLevelUnlocked(lvl.level))
  );
}

const totalSelectedPrompts = computed(() => {
  return levels.value
    .filter(l => selectedLevels.value.includes(l.level))
    .reduce((sum, l) => sum + l.total_prompts, 0);
});

function formatApiError(err, fallback) {
  if (typeof err?.detail === "string") return err.detail;
  if (typeof err?.detail?.detail === "string") return err.detail.detail;
  return fallback;
}

function showFeedback(type, text) {
  feedback.type = type;
  feedback.text = text;
}

function clearFeedback() {
  feedback.text = "";
}

function toggleLevel(level, totalPrompts) {
  if (totalPrompts === 0) return;
  
  const idx = selectedLevels.value.indexOf(level);
  if (idx === -1) {
    selectedLevels.value.push(level);
  } else {
    selectedLevels.value.splice(idx, 1);
  }
}

async function loadLevels() {
  const data = await apiFetch("/api/learn/levels");
  levels.value = data.levels;
  totalInQueue.value = data.total_in_queue;
  if (data.preferences) {
    dailyLimit.value = data.preferences.daily_new_limit || dailyLimit.value;
    selectedLevels.value = data.preferences.selected_levels || [];
    selectedContentKind.value = !data.preferences.content_preference || data.preferences.content_preference === "both"
      ? null
      : data.preferences.content_preference;
  }
}

async function loadQueue() {
  const kindParam = selectedKind.value ? `&kind=${selectedKind.value}` : '';
  const data = await apiFetch(`/api/learn/queue?limit=10${kindParam}`);
  availableToAdd.value = data.available_to_add;
  newInQueue.value = data.new_in_queue;
}

async function startLearning() {
  if (selectedLevels.value.length === 0) return;
  
  adding.value = true;
  clearFeedback();
  try {
    // Save preferences to backend
    await apiFetch('/api/learn/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        daily_new_limit: normalizedDailyLimit.value,
        content_preference: selectedContentKind.value || 'both',
        selected_levels: selectedLevels.value,
      }),
    });
    
    // Auto-add first batch of items
    const result = await apiFetch(
      `/api/learn/auto-add?${timezoneQuery()}`,
      { method: 'POST' }
    );
    
    await counts.refresh();
    
    // Go directly to study the new items if any were added
    if (result.added > 0) {
      router.push("/study");
    } else {
      showFeedback("info", result.message || 'No items available');
    }
  } catch (err) {
    console.error('Failed to start learning:', err);
    showFeedback("error", formatApiError(err, 'Failed to start learning'));
  } finally {
    adding.value = false;
  }
}

async function addWholeLevel(level) {
  addingLevelName.value = level;
  clearFeedback();
  try {
    const kindParam = selectedContentKind.value ? `&kind=${selectedContentKind.value}` : '';
    const result = await apiFetch(
      `/api/learn/add-level/${level}?limit=${normalizedDailyLimit.value}&${timezoneQuery()}${kindParam}`,
      { method: "POST" }
    );
    await loadLevels();
    await loadQueue();
    await counts.refresh();
    if (result.added === 0 && result.message) {
      showFeedback("info", result.message);
    } else {
      showFeedback("success", `${level} unlocked. ${result.added} new items are ready for study.`);
    }
  } catch (err) {
    console.error('Failed to unlock level:', err);
    showFeedback("error", formatApiError(err, 'Failed to unlock level'));
  } finally {
    addingLevelName.value = null;
  }
}

async function removeWholeLevel(level) {
  removingLevelName.value = level;
  clearFeedback();
  try {
    const result = await apiFetch(`/api/learn/level/${level}`, { method: "DELETE" });
    await loadLevels();
    await loadQueue();
    await counts.refresh();
    showFeedback(
      "success",
      `${level} removed. ${result.removed_learning_items} unstudied ${result.removed_learning_items === 1 ? "item was" : "items were"} cleared.`
    );
  } catch (err) {
    console.error('Failed to remove level:', err);
    showFeedback("error", formatApiError(err, 'Failed to remove level'));
  } finally {
    removingLevelName.value = null;
  }
}

async function toggleWholeLevel(lvl) {
  if (isLevelUnlocked(lvl.level)) {
    await removeWholeLevel(lvl.level);
    return;
  }
  await addWholeLevel(lvl.level);
}

async function saveLearningPreferences() {
  savingPreferences.value = true;
  clearFeedback();
  try {
    dailyLimit.value = normalizedDailyLimit.value;
    await apiFetch('/api/learn/preferences', {
      method: 'POST',
      body: JSON.stringify({
        daily_new_limit: normalizedDailyLimit.value,
        content_preference: selectedContentKind.value || 'both',
        selected_levels: selectedLevels.value,
      }),
    });
    showFeedback("success", "Daily learning preferences saved.");
  } catch (err) {
    console.error('Failed to save learning preferences:', err);
    showFeedback("error", formatApiError(err, 'Failed to save learning preferences'));
  } finally {
    savingPreferences.value = false;
  }
}

async function learnNext() {
  learning.value = true;
  added.value = [];
  clearFeedback();
  try {
    const kindParam = selectedKind.value ? `&kind=${selectedKind.value}` : '';
    const data = await apiFetch(
      `/api/learn/next?count=${count.value}&${timezoneQuery()}${kindParam}`,
      { method: "POST" }
    );
    added.value = data.added;
    await loadQueue();  // This updates availableToAdd and newInQueue
    await counts.refresh();
    if (data.added.length === 0) {
      showFeedback("info", "No more unlocked items are available right now.");
    }
  } catch (err) {
    console.error('Failed to add more items:', err);
    showFeedback("error", formatApiError(err, 'Failed to add more items'));
  } finally {
    learning.value = false;
  }
}

watch(selectedKind, () => {
  if (totalInQueue.value > 0) {
    loadQueue();
  }
});

onMounted(async () => {
  await loadLevels();
  if (totalInQueue.value > 0) {
    await loadQueue();
  }
  await counts.refresh();
  loading.value = false;
});
</script>

<style scoped>
.learn-page {
  max-width: 900px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}

.header h2 {
  margin: 0;
}

.header .muted {
  margin: 6px 0 0 0;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.feedback-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: var(--space-4);
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 14px;
  box-shadow: var(--shadow-sm);
}

.feedback-banner.success {
  border-color: var(--success-border-strong);
  background: var(--success-tint);
  color: var(--text-primary);
}

.feedback-banner.error {
  border-color: var(--error-border);
  background: var(--error-tint);
  color: var(--text-primary);
}

.feedback-dismiss {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--transparent);
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: var(--transition-fast);
}

.feedback-dismiss:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.feedback-dismiss svg {
  width: 16px;
  height: 16px;
}

/* Loading */
.loading {
  text-align: center;
  padding: 60px;
  color: var(--text-muted);
}

/* Onboarding */
.onboarding {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.welcome-card {
  text-align: center;
  padding: 36px var(--space-5);
}

.welcome-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: var(--accent-blue-gradient);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-icon svg {
  width: 40px;
  height: 40px;
  color: var(--text-on-accent);
}

.welcome-card h3 {
  margin: 0 0 8px 0;
  font-size: 22px;
}

.welcome-card .muted {
  margin: 0;
  max-width: 500px;
  margin: 0 auto;
}

/* Levels section */
.levels-section h4,
.settings-section h4 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.levels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--space-3);
}

.level-card {
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  cursor: pointer;
  transition: var(--transition-base);
  position: relative;
}

.level-card:hover:not(.disabled) {
  border-color: var(--accent);
}

.level-card.selected {
  border-color: var(--accent);
  background: var(--accent-glow);
}

.level-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.level-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.level-check {
  width: 20px;
  height: 20px;
  background: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.level-check svg {
  width: 12px;
  height: 12px;
  color: var(--text-on-accent);
}

.level-card h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
}

.level-stats {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.level-prompts {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
}

/* Settings section */
.settings-section {
  padding: var(--space-5);
}

.settings-section .muted {
  margin: 0 0 16px 0;
}

.daily-limit-options {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.daily-limit-segments {
  flex: 1;
  min-width: 260px;
}

.daily-limit-segments .segment-btn {
  min-width: 54px;
  justify-content: center;
  font-weight: 700;
}

.limit-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-4) var(--space-3);
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-base);
}

.limit-option:hover {
  border-color: var(--accent);
}

.limit-option.active {
  border-color: var(--accent);
  background: var(--accent-glow);
}

.limit-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.limit-icon {
  width: 32px;
  height: 32px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.limit-option.active .limit-value {
  color: var(--accent);
}

.limit-option.active .limit-icon {
  color: var(--accent);
}

.limit-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.custom-limit {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
  max-width: 220px;
  font-size: 13px;
  color: var(--text-muted);
}

.custom-limit.inline {
  margin-top: 0;
  width: 120px;
  flex-shrink: 0;
}

/* Start section */
.start-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-card {
  padding: var(--space-4) var(--space-5);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 14px;
}

.summary-row:last-child {
  border-bottom: none;
}

.summary-row.highlight {
  color: var(--accent);
  font-weight: 600;
}

.summary-value {
  font-weight: 500;
}

.start-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

/* Active Learning */
.active-learning {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* Study prompt - primary CTA */
.study-prompt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-5);
  padding: var(--space-5);
  background: linear-gradient(135deg, var(--blue-tint), var(--purple-tint));
  border: 1px solid var(--blue-border);
  border-radius: var(--radius-lg);
}

.study-prompt-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.study-icon {
  width: 48px;
  height: 48px;
  background: var(--accent);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.study-icon svg {
  width: 28px;
  height: 28px;
  color: var(--text-on-accent);
}

.study-text h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
}

.study-text p {
  margin: 0;
  color: var(--text-muted);
  font-size: 14px;
}

.study-text strong {
  color: var(--accent);
}

.study-btn {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Stats bar */
.stats-bar {
  display: flex;
  gap: 12px;
}

.daily-settings {
  padding: var(--space-5);
}

.daily-settings .muted {
  margin: 4px 0 0 0;
  font-size: 13px;
}

.daily-settings-controls {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.stat.clickable {
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.stat.clickable:hover {
  border-color: var(--accent);
  background: var(--accent-surface-subtle);
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.stat-action {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--accent);
  padding: 8px 0;
}

/* Add more section - collapsible */
.add-more-section {
  margin-top: 8px;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: var(--transition-base);
}

.add-more-section:hover {
  border-color: var(--accent-border-subtle);
  box-shadow: var(--shadow-md);
}

.add-more-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-5);
  background: var(--transparent);
  border: 0;
  cursor: pointer;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  transition: var(--transition-base);
}

.add-more-toggle:hover {
  background: var(--bg-secondary);
}

.add-more-toggle::marker {
  content: none;
}

.add-more-toggle::-webkit-details-marker {
  display: none;
}

.add-more-content {
  margin-top: 0;
  padding: var(--space-4);
  border: 0;
  border-top: 1px solid var(--border-color);
  border-radius: 0;
  box-shadow: none;
  background: var(--bg-card);
}

.add-controls {
  display: flex;
  gap: var(--space-4);
  align-items: flex-end;
  flex-wrap: wrap;
}

.count-control, .type-filter {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.count-control label, .type-filter label {
  font-size: 13px;
  color: var(--text-muted);
}

.item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px var(--space-3);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
}

.item-type {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.item-type.grammar {
  background: var(--blue-tint-strong);
  color: var(--blue);
}

.item-type.vocab {
  background: var(--violet-tint);
  color: var(--violet);
}

.item-title {
  font-weight: 500;
  flex-shrink: 0;
}

.item-sentence {
  color: var(--text-muted);
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Unlock levels section */
.unlock-levels h3 {
  margin: 0 0 4px 0;
}

.unlock-levels > .muted {
  margin: 0 0 16px 0;
}

.mini-levels {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.mini-level {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: var(--space-3);
  background: var(--bg-secondary);
  border: 1px solid var(--transparent);
  border-radius: var(--radius-md);
  transition: var(--transition-fast);
}

.mini-level.complete {
  opacity: 0.6;
}

.mini-level.unlocked {
  border-color: var(--accent-border);
  background: var(--accent-tint);
}

.remove-level-btn {
  color: var(--error);
}

.remove-level-btn:hover {
  border-color: var(--error-border);
  color: var(--error);
  background: var(--error-tint);
}

.mini-level-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 140px;
}

.mini-level-name {
  font-size: 13px;
}

.mini-level-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 60px;
  text-align: right;
}

@media (max-width: 640px) {
  .levels-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .daily-limit-options {
    grid-template-columns: repeat(2, 1fr);
  }

  .study-prompt {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .study-prompt-content {
    flex-direction: column;
  }
  
  .stats-bar {
    flex-direction: column;
  }

  .daily-settings-controls {
    align-items: stretch;
    flex-direction: column;
  }

  .custom-limit.inline {
    width: 100%;
  }
  
  .add-controls {
    flex-direction: column;
    gap: 16px;
  }
  
  .mini-level {
    flex-wrap: wrap;
  }
  
  .mini-level-progress {
    width: 100%;
    order: 3;
  }
}
</style>
