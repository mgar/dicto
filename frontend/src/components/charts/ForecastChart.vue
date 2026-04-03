<template>
  <div class="card chart-card">
    <div class="chart-header">
    <div>
      <h3>Forecast</h3>
      <p class="chart-subtitle">Upcoming scheduled reviews</p>
    </div>
      <div class="chart-controls">
        <button class="icon-btn" @click="$emit('shift', -7)" :disabled="!canShiftBack">
          <Icon name="chevron-left" />
        </button>
        <button class="icon-btn" @click="$emit('shift', 7)">
          <Icon name="chevron-right" />
        </button>
      </div>
    </div>
    
    <div class="legend">
      <span class="legend-item"><span class="legend-dot vocab"></span> Vocab</span>
      <span class="legend-item"><span class="legend-dot grammar"></span> Grammar</span>
    </div>

    <div v-if="loading" class="chart-loading">Loading…</div>
    
    <div v-else class="bar-chart">
      <div 
        v-for="(item, idx) in dataWithProjections" 
        :key="item.date" 
        class="bar-group"
      >
        <div class="bar-container">
          <!-- Show value -->
          <span v-if="item.total > 0" class="bar-value">
            {{ item.total }}
          </span>
          
          <!-- Scheduled reviews -->
          <div 
            v-if="item.total > 0"
            class="bar-stack"
            :style="{ height: Math.max(getBarHeight(item.total), 4) + '%' }"
          >
            <div
              class="bar-segment vocab"
              :style="{ flex: item.vocab_due || 0 }"
            ></div>
            <div
              class="bar-segment grammar"
              :style="{ flex: item.grammar_due || 1 }"
            ></div>
          </div>
          
          <!-- Empty state -->
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

// Simple data mapping - just show scheduled reviews
const dataWithProjections = computed(() => {
  if (!props.data.length) return [];

  return props.data.map((item) => {
    const total = (item.vocab_due || 0) + (item.grammar_due || 0);
    
    return {
      ...item,
      total,
    };
  });
});

const maxValue = computed(() => {
  const max = Math.max(
    ...dataWithProjections.value.map(i => i.total || 0),
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
  letter-spacing: -0.02em;
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
  background: #a78bfa;
}

.bar-segment.grammar {
  background: #6366f1;
}

.bar-label {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  white-space: nowrap;
  font-weight: 500;
}
</style>
