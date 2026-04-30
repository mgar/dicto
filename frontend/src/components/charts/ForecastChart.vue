<template>
  <div class="card chart-card">
    <div class="chart-header">
      <div>
        <h3>Forecast</h3>
        <p class="chart-subtitle">Scheduled and projected reviews</p>
      </div>
      <div class="chart-controls">
        <button
          class="icon-btn"
          :disabled="!canShiftBack"
          title="View older"
          aria-label="View older forecast"
          @click="$emit('shift', -7)"
        >
          <Icon name="chevron-left" />
        </button>
        <button
          class="icon-btn"
          title="View newer"
          aria-label="View newer forecast"
          @click="$emit('shift', 7)"
        >
          <Icon name="chevron-right" />
        </button>
      </div>
    </div>

    <div class="legend">
      <span class="legend-item"><span class="legend-dot vocab"></span> Vocab</span>
      <span class="legend-item"><span class="legend-dot grammar"></span> Grammar</span>
      <span v-if="hasProjectedReviews" class="legend-item">
        <span class="legend-dot projected"></span> Projected
      </span>
    </div>

    <div v-if="loading" class="chart-loading">Loading…</div>

    <div v-else class="bar-chart">
      <div
        v-for="item in chartItems"
        :key="item.date"
        class="bar-group"
      >
        <div class="bar-container">
          <span
            v-if="item.total > 0"
            class="bar-value"
            :title="`Scheduled: ${item.scheduledTotal}, projected: ${item.projectedTotal}`"
          >
            {{ item.total }}
          </span>

          <div
            v-if="item.total > 0"
            class="bar-stack"
            :style="{ height: Math.max(getBarHeight(item.total), 4) + '%' }"
          >
            <div
              v-if="item.projectedVocab > 0"
              class="bar-segment vocab projected"
              :style="{ flex: item.projectedVocab }"
            ></div>
            <div
              v-if="item.projectedGrammar > 0"
              class="bar-segment grammar projected"
              :style="{ flex: item.projectedGrammar }"
            ></div>
            <div
              v-if="item.scheduledVocab > 0"
              class="bar-segment vocab"
              :style="{ flex: item.scheduledVocab }"
            ></div>
            <div
              v-if="item.scheduledGrammar > 0"
              class="bar-segment grammar"
              :style="{ flex: item.scheduledGrammar }"
            ></div>
          </div>

          <div
            v-if="item.total === 0"
            class="bar-stack empty"
            :style="{ height: '4%' }"
          ></div>
        </div>
        <span class="bar-label">{{ formatBarLabel(item.date) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import Icon from "../Icon.vue";

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  canShiftBack: {
    type: Boolean,
    default: false
  }
});

defineEmits(['shift']);

const chartItems = computed(() => {
  if (!props.data.length) return [];

  return props.data.map((item) => {
    const scheduledGrammar = item.grammar_due || 0;
    const scheduledVocab = item.vocab_due || 0;
    const projectedGrammar = item.projected_grammar_due || 0;
    const projectedVocab = item.projected_vocab_due || 0;
    const scheduledTotal = item.due ?? scheduledGrammar + scheduledVocab;
    const projectedTotal = item.projected_due ?? projectedGrammar + projectedVocab;

    return {
      ...item,
      scheduledGrammar,
      scheduledVocab,
      projectedGrammar,
      projectedVocab,
      scheduledTotal,
      projectedTotal,
      total: scheduledTotal + projectedTotal,
    };
  });
});

const hasProjectedReviews = computed(() => {
  return chartItems.value.some(item => item.projectedTotal > 0);
});

const maxValue = computed(() => {
  const max = Math.max(
    ...chartItems.value.map(i => i.total || 0),
    1
  );
  return Math.ceil(max / 10) * 10 || 10;
});

function getBarHeight(value) {
  return (value / maxValue.value) * 100;
}

function formatBarLabel(isoDate) {
  const d = new Date(isoDate + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const dateOnly = new Date(isoDate + "T00:00:00");

  if (dateOnly.getTime() === today.getTime()) return "Today";
  if (dateOnly.getTime() === tomorrow.getTime()) return "Tomorrow";

  return d.toLocaleDateString(undefined, { day: "numeric", weekday: "short" });
}
</script>

<style scoped>
.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 160px;
  padding-top: 24px;
}

.bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  gap: 7px;
}

.bar-container {
  height: 120px;
  width: 100%;
  max-width: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  position: relative;
}

.bar-value {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 3px;
  letter-spacing: 0;
}

.bar-stack {
  width: 65%;
  display: flex;
  flex-direction: column;
  border-radius: 5px;
  overflow: hidden;
  min-height: 4px;
  transition: height 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.bar-stack.empty {
  background: var(--border-color);
  opacity: 0.4;
  border-radius: 5px;
}

.bar-segment {
  width: 100%;
  min-height: 0;
}

.bar-segment.vocab {
  background: var(--violet);
}

.bar-segment.grammar {
  background: var(--accent);
}

.bar-segment.projected {
  border: 1px dashed var(--chart-projected-border);
  box-sizing: border-box;
  opacity: 0.82;
}

.bar-segment.projected.vocab {
  background:
    repeating-linear-gradient(
      135deg,
      var(--chart-projected-stripe-vocab) 0 3px,
      var(--transparent) 3px 7px
    ),
    var(--violet);
}

.bar-segment.projected.grammar {
  background:
    repeating-linear-gradient(
      135deg,
      var(--chart-projected-stripe-grammar) 0 3px,
      var(--transparent) 3px 7px
    ),
    var(--accent);
}

.bar-label {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  white-space: nowrap;
  font-weight: 500;
}

.legend-dot.projected {
  border: 1px dashed var(--text-muted);
  box-sizing: border-box;
}
</style>
