<template>
  <div class="card chart-card">
    <div class="chart-header">
      <div>
        <h3>Activity</h3>
        <p class="chart-subtitle">Your review history</p>
      </div>
      <div class="chart-controls">
        <button class="icon-btn" @click="$emit('shift', -14)" :disabled="!canShiftBack" title="View older">
          <Icon name="chevron-left" />
        </button>
        <button class="icon-btn" @click="$emit('shift', 14)" :disabled="!canShiftForward" title="View newer">
          <Icon name="chevron-right" />
        </button>
      </div>
    </div>

    <div class="legend">
      <span class="legend-item"><span class="legend-dot vocab"></span> Vocab</span>
      <span class="legend-item"><span class="legend-dot grammar"></span> Grammar</span>
    </div>

    <div v-if="loading" class="chart-loading">Loading…</div>
    
    <div v-else class="activity-dots">
      <div 
        v-for="item in data" 
        :key="item.date" 
        class="activity-day"
        :title="`Vocab: ${item.vocab_reviews || 0}, Grammar: ${item.grammar_reviews || 0}`"
      >
        <div class="activity-dot-stack">
          <div 
            class="activity-dot vocab"
            :class="{ 
              active: (item.vocab_reviews || 0) > 0,
              high: (item.vocab_reviews || 0) >= 15,
              medium: (item.vocab_reviews || 0) >= 5 && (item.vocab_reviews || 0) < 15
            }"
          >
            <span v-if="(item.vocab_reviews || 0) > 0" class="activity-count">{{ item.vocab_reviews }}</span>
          </div>
          <div 
            class="activity-dot grammar"
            :class="{ 
              active: (item.grammar_reviews || 0) > 0,
              high: (item.grammar_reviews || 0) >= 15,
              medium: (item.grammar_reviews || 0) >= 5 && (item.grammar_reviews || 0) < 15
            }"
          >
            <span v-if="(item.grammar_reviews || 0) > 0" class="activity-count">{{ item.grammar_reviews }}</span>
          </div>
        </div>
        <span class="activity-label">{{ formatActivityLabel(item.date) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import Icon from "../Icon.vue";

defineProps({
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
  },
  canShiftForward: {
    type: Boolean,
    default: false
  }
});

defineEmits(['shift']);

function formatActivityLabel(isoDate) {
  const d = new Date(isoDate + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const dateOnly = new Date(isoDate + "T00:00:00");
  
  if (dateOnly.getTime() === today.getTime()) return "Today";
  
  return d.toLocaleDateString(undefined, { day: "numeric", weekday: "short" });
}
</script>

<style scoped>
.activity-dots {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 4px 0;
}

.activity-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  flex: 1;
  min-width: 40px;
}

.activity-dot-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  height: 52px;
  justify-content: center;
}

.activity-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--border-color);
  opacity: 0.25;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.activity-dot.vocab {
  background: #a78bfa;
}

.activity-dot.grammar {
  background: #6366f1;
}

.activity-dot.active {
  opacity: 0.55;
}

.activity-dot.medium {
  opacity: 0.8;
  transform: scale(1.08);
}

.activity-dot.high {
  opacity: 1;
  transform: scale(1.15);
}

.activity-count {
  font-size: 8.5px;
  font-weight: 700;
  color: white;
}

.activity-label {
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
  font-weight: 500;
}
</style>
