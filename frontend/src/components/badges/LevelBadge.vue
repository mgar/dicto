<template>
  <span class="level-badge" :class="[level.toLowerCase(), { small: size === 'small' }]">
    {{ level }}
  </span>
</template>

<script setup>
defineProps({
  level: {
    type: String,
    required: true,
    validator: (value) => ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].includes(value.toUpperCase())
  },
  size: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'small'].includes(value)
  }
});
</script>

<style scoped>
.level-badge {
  display: inline-block;
  font-size: 10.5px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  color: var(--text-on-accent);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.level-badge.small {
  font-size: 9.5px;
  padding: 2px 6px;
}

/* Level colors - indigo to violet spectrum */
.level-badge.a1 { background: linear-gradient(135deg, var(--level-a1-start), var(--level-a1-end)); }
.level-badge.a2 { background: linear-gradient(135deg, var(--level-a2-start), var(--level-a2-end)); }
.level-badge.b1 { background: linear-gradient(135deg, var(--level-b1-start), var(--level-b1-end)); }
.level-badge.b2 { background: linear-gradient(135deg, var(--level-b2-start), var(--level-b2-end)); }
.level-badge.c1 { background: linear-gradient(135deg, var(--level-c1-start), var(--level-c1-end)); }
.level-badge.c2 { background: linear-gradient(135deg, var(--level-c2-start), var(--level-c2-end)); }
</style>
