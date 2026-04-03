<template>
  <div class="mastery-panel card">
    <div class="mastery-header">
      <h3>Progress</h3>
      <div class="kind-toggle">
        <button
          class="toggle-btn"
          :class="{ active: kind === 'grammar' }"
          @click="$emit('change-kind', 'grammar')"
        >
          Grammar
        </button>
        <button
          class="toggle-btn"
          :class="{ active: kind === 'vocab' }"
          @click="$emit('change-kind', 'vocab')"
        >
          Vocab
        </button>
      </div>
    </div>

    <div v-if="loading" class="muted">Loading progress…</div>

    <div v-else class="tier-grid">
      <div v-for="tier in tiers" :key="tier.key" class="tier-card" :class="tier.key">
        <div class="tier-name">{{ tier.label }}</div>
        <div class="tier-count">{{ tier.count }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  kind: { type: String, default: "grammar" },
  tiers: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

defineEmits(["change-kind"]);
</script>

<style scoped>
.mastery-panel {
  margin-bottom: 16px;
}

.mastery-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.mastery-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.kind-toggle {
  display: inline-flex;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 9px;
  padding: 3px;
  gap: 2px;
}

.toggle-btn {
  border: none;
  background: transparent;
  color: var(--text-muted);
  padding: 5px 12px;
  font-size: 12.5px;
  font-weight: 500;
  border-radius: 7px;
  cursor: pointer;
  transition: all 0.18s ease;
  font-family: inherit;
}

.toggle-btn:hover:not(.active) {
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.04);
}

.toggle-btn.active {
  background: var(--accent);
  color: white;
  box-shadow: 0 2px 6px var(--accent-glow);
}

.tier-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(110px, 1fr));
  gap: 8px;
}

@media (max-width: 920px) {
  .tier-grid {
    grid-template-columns: repeat(2, minmax(110px, 1fr));
  }
}

.tier-card {
  border-radius: 12px;
  padding: 14px;
  border: 1px solid;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.tier-card:hover {
  transform: translateY(-2px);
}

.tier-name {
  font-size: 11.5px;
  font-weight: 600;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.75;
}

.tier-count {
  font-size: 30px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.04em;
}

.foundations {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.25);
  color: #a5b4fc;
}
.foundations:hover {
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.15);
}

.builder {
  background: rgba(124, 58, 237, 0.12);
  border-color: rgba(124, 58, 237, 0.28);
  color: #c4b5fd;
}
.builder:hover {
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.15);
}

.communicator {
  background: rgba(139, 92, 246, 0.12);
  border-color: rgba(139, 92, 246, 0.3);
  color: #d8b4fe;
}
.communicator:hover {
  box-shadow: 0 4px 14px rgba(139, 92, 246, 0.15);
}

.fluent {
  background: rgba(168, 85, 247, 0.14);
  border-color: rgba(168, 85, 247, 0.32);
  color: #e9d5ff;
}
.fluent:hover {
  box-shadow: 0 4px 14px rgba(168, 85, 247, 0.15);
}

.mastery {
  background: rgba(192, 132, 252, 0.16);
  border-color: rgba(192, 132, 252, 0.35);
  color: #f3e8ff;
}
.mastery:hover {
  box-shadow: 0 4px 14px rgba(192, 132, 252, 0.2);
}

/* Light mode text */
[data-theme="light"] .foundations { color: #4f46e5; }
[data-theme="light"] .builder     { color: #6d28d9; }
[data-theme="light"] .communicator { color: #5b21b6; }
[data-theme="light"] .fluent      { color: #7c3aed; }
[data-theme="light"] .mastery     { color: #6d28d9; }
</style>
