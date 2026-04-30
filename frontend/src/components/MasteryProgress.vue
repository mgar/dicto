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
  background: var(--transparent);
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
  background: var(--border-subtle);
}

.toggle-btn.active {
  background: var(--accent);
  color: var(--text-on-accent);
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
  background: var(--tier-foundations-bg);
  border-color: var(--tier-foundations-border);
  color: var(--tier-foundations-text);
}
.foundations:hover {
  box-shadow: 0 4px 14px var(--tier-foundations-shadow);
}

.builder {
  background: var(--tier-builder-bg);
  border-color: var(--tier-builder-border);
  color: var(--tier-builder-text);
}
.builder:hover {
  box-shadow: 0 4px 14px var(--tier-builder-shadow);
}

.communicator {
  background: var(--tier-communicator-bg);
  border-color: var(--tier-communicator-border);
  color: var(--tier-communicator-text);
}
.communicator:hover {
  box-shadow: 0 4px 14px var(--tier-communicator-shadow);
}

.fluent {
  background: var(--tier-fluent-bg);
  border-color: var(--tier-fluent-border);
  color: var(--tier-fluent-text);
}
.fluent:hover {
  box-shadow: 0 4px 14px var(--tier-fluent-shadow);
}

.mastery {
  background: var(--tier-mastery-bg);
  border-color: var(--tier-mastery-border);
  color: var(--tier-mastery-text);
}
.mastery:hover {
  box-shadow: 0 4px 14px var(--tier-mastery-shadow);
}

/* Light mode text */
[data-theme="light"] .foundations { color: var(--tier-foundations-text); }
[data-theme="light"] .builder     { color: var(--tier-builder-text); }
[data-theme="light"] .communicator { color: var(--tier-communicator-text); }
[data-theme="light"] .fluent      { color: var(--tier-fluent-text); }
[data-theme="light"] .mastery     { color: var(--tier-mastery-text); }
</style>
