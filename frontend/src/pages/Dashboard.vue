<template>
  <div>
    <div class="row" style="align-items:center; justify-content: space-between;">
      <div>
        <h2 style="margin:0;">Dashboard</h2>
        <p class="muted" style="margin:6px 0 0 0;">
          Forecast and recent activity.
        </p>
      </div>
      <button class="btn secondary" @click="refreshAll" :disabled="loading">
        Refresh
      </button>
    </div>

    <div style="height: 16px;"></div>

    <div class="row" style="gap: 12px; margin-bottom: 20px; margin-top: 14px;">
      <RouterLink 
        class="action-card learn" 
        :class="{ highlighted: shouldHighlightLearn }"
        :to="learnLink"
      >
        <span v-if="shouldHighlightLearn" class="start-here-badge">
          <Icon name="chevrons-right" />
          Start here
        </span>
        <div class="action-label">Learn</div>
        <div class="action-sub">{{ counts.state.learnRemaining > 0 ? 'Study New Items' : 'Add Content' }}</div>
        <span class="action-badge learn-badge">{{ counts.state.learnRemaining ?? '–' }}</span>
      </RouterLink>
      
      <RouterLink class="action-card review" to="/review">
        <div class="action-label">Review</div>
        <div class="action-sub">Practice</div>
        <span class="action-badge">{{ counts.state.dueNow || 0 }}</span>
      </RouterLink>
    </div>

    <MasteryProgress
      :kind="masteryKind"
      :tiers="masteryTiers"
      :loading="loading || masteryLoading"
      @change-kind="changeMasteryKind"
    />

    <!-- Forecast Chart -->
    <ForecastChart 
      :data="visibleForecast" 
      :loading="loading"
      :can-shift-back="forecastOffset > 0"
      @shift="shiftForecast"
    />

    <div style="height: 16px;"></div>

    <!-- Activity Chart -->
    <ActivityChart 
      :data="visibleActivity" 
      :loading="loading"
      :can-shift-back="activityOffset > 0"
      :can-shift-forward="activityOffset < activity.length - 14"
      @shift="shiftActivity"
    />

    <div style="height: 20px;"></div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { apiFetch, localDateString, timezoneQuery } from "../api";
import { useCounts } from "../counts";
import Icon from "../components/Icon.vue";
import ForecastChart from "../components/charts/ForecastChart.vue";
import ActivityChart from "../components/charts/ActivityChart.vue";
import MasteryProgress from "../components/MasteryProgress.vue";

const counts = useCounts();

// Link to Study if there are new items, otherwise to Learn page
const learnLink = computed(() => {
  return counts.state.learnRemaining > 0 ? "/study" : "/learn";
});

// Highlight Learn card when user should start there:
// - New user (no items to review) 
// - Has items to study
const shouldHighlightLearn = computed(() => {
  const hasItemsToStudy = counts.state.learnRemaining > 0;
  const hasNoReviews = counts.state.dueNow === 0;
  return hasItemsToStudy || hasNoReviews;
});

const forecastDays = 21;
const activityDays = 30;

const loading = ref(false);
const forecast = ref([]);
const activity = ref([]);
const forecastOffset = ref(0);
const activityOffset = ref(0);
const masteryKind = ref("grammar");
const masteryTiers = ref([]);
const masteryLoading = ref(false);

const visibleForecast = computed(() => {
  return forecast.value.slice(forecastOffset.value, forecastOffset.value + 7);
});

const visibleActivity = computed(() => {
  return activity.value.slice(activityOffset.value, activityOffset.value + 14);
});

function shiftForecast(days) {
  const newOffset = forecastOffset.value + days;
  if (newOffset >= 0 && newOffset < forecast.value.length - 6) {
    forecastOffset.value = newOffset;
  }
}

function shiftActivity(days) {
  const newOffset = activityOffset.value + days;
  if (newOffset >= 0 && newOffset < activity.value.length - 13) {
    activityOffset.value = newOffset;
  }
}

async function refreshAll() {
  loading.value = true;
  try {
    // Try to auto-add new items if user has preferences set
    try {
      await apiFetch(`/api/learn/auto-add?${timezoneQuery()}`, { method: 'POST' });
    } catch (err) {
      // Silently fail if no preferences set or user has unstudied items
      // This is expected behavior
    }
    
    // Pass local date to handle timezone differences
    const now = new Date();
    const today = localDateString(now);
    const timezoneParams = timezoneQuery(now);
    const [f, a, m] = await Promise.all([
      apiFetch(
        `/api/stats/forecast?days=${forecastDays}&start_date=${today}&${timezoneParams}`
      ),
      apiFetch(`/api/stats/activity?days=${activityDays}&end_date=${today}&${timezoneParams}`),
      apiFetch(`/api/stats/mastery-overview?kind=${masteryKind.value}`),
    ]);
    forecast.value = f.items;
    activity.value = a.items;
    masteryTiers.value = m.tiers || [];
    // Start showing the most recent 14 days
    activityOffset.value = Math.max(0, a.items.length - 14);
    await counts.refresh();
  } finally {
    loading.value = false;
  }
}

async function refreshMastery() {
  masteryLoading.value = true;
  try {
    const data = await apiFetch(`/api/stats/mastery-overview?kind=${masteryKind.value}`);
    masteryTiers.value = data.tiers || [];
  } finally {
    masteryLoading.value = false;
  }
}

function changeMasteryKind(kind) {
  if (kind === masteryKind.value) return;
  masteryKind.value = kind;
  refreshMastery();
}

onMounted(refreshAll);
</script>

<style scoped>
/* Action cards */
.action-card {
  flex: 1;
  min-width: 200px;
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-lg);
  text-decoration: none;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: var(--transition-base);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.action-card::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  opacity: 0;
  transition: var(--transition-base);
  background: linear-gradient(135deg, var(--accent-surface-subtle), var(--transparent));
}

.action-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.action-card:hover::after {
  opacity: 1;
}

.action-card.learn {
  border-left: 3px solid var(--violet);
}

.action-card.learn:hover {
  border-color: var(--violet);
  border-left-color: var(--violet);
  box-shadow: 0 8px 24px var(--violet-glow);
}

/* Highlighted state for Learn card */
.action-card.learn.highlighted {
  background: linear-gradient(135deg, var(--violet-tint), var(--accent-surface-subtle));
  border: 2px solid var(--violet-border);
  border-left-width: 4px;
}

.action-card.learn.highlighted:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px var(--violet-glow);
}

.start-here-badge {
  position: absolute;
  top: -10px;
  left: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--brand-gradient);
  color: var(--text-on-accent);
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 99px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  box-shadow: 0 2px 8px var(--accent-border);
}

.start-here-badge svg {
  width: 12px;
  height: 12px;
}

.action-card.review {
  border-left: 3px solid var(--accent);
}

.action-card.review:hover {
  border-color: var(--accent);
  border-left-color: var(--accent);
  box-shadow: 0 8px 24px var(--accent-glow);
}

.action-label {
  font-weight: 700;
  font-size: 15px;
  margin-bottom: 3px;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.action-sub {
  font-size: 12.5px;
  color: var(--text-muted);
}

.action-badge {
  position: absolute;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  font-weight: 800;
  font-size: 26px;
  color: var(--accent-light);
  letter-spacing: -0.04em;
  line-height: 1;
}

.action-card.learn .action-badge {
  color: var(--violet-light);
}
</style>
