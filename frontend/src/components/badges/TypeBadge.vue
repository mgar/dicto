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
  background: rgba(99, 102, 241, 0.12);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.type-badge.vocab {
  background: rgba(167, 139, 250, 0.12);
  color: #c4b5fd;
  border: 1px solid rgba(167, 139, 250, 0.2);
}

[data-theme="light"] .type-badge.grammar {
  color: #4f46e5;
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.15);
}

[data-theme="light"] .type-badge.vocab {
  color: #7c3aed;
  background: rgba(124, 58, 237, 0.08);
  border-color: rgba(124, 58, 237, 0.15);
}
</style>
