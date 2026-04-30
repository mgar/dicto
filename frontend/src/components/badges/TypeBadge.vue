<template>
  <span class="type-badge" :class="type">
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => ['grammar', 'vocab'].includes(value)
  },
  // Optional custom label, defaults to type name
  customLabel: {
    type: String,
    default: null
  }
});

const label = computed(() => {
  if (props.customLabel) return props.customLabel;
  return props.type === 'grammar' ? 'Grammar' : 'Vocabulary';
});
</script>

<style scoped>
.type-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 8px;
  letter-spacing: 0.01em;
}

.type-badge.grammar {
  background: var(--accent-tint);
  color: var(--accent-light);
  border: 1px solid var(--accent-border-subtle);
}

.type-badge.vocab {
  background: var(--violet-tint);
  color: var(--violet-light);
  border: 1px solid var(--violet-glow);
}

[data-theme="light"] .type-badge.grammar {
  color: var(--accent);
  background: var(--accent-tint);
  border-color: var(--accent-border-subtle);
}

[data-theme="light"] .type-badge.vocab {
  color: var(--violet);
  background: var(--violet-tint);
  border-color: var(--violet-glow);
}
</style>
