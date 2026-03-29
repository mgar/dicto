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
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.level-badge.small {
  font-size: 9.5px;
  padding: 2px 6px;
}

/* Level colors - indigo to violet spectrum */
.level-badge.a1 { background: linear-gradient(135deg, #6366f1, #818cf8); }
.level-badge.a2 { background: linear-gradient(135deg, #7c3aed, #8b5cf6); }
.level-badge.b1 { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }
.level-badge.b2 { background: linear-gradient(135deg, #9333ea, #c084fc); }
.level-badge.c1 { background: linear-gradient(135deg, #a855f7, #d946ef); }
.level-badge.c2 { background: linear-gradient(135deg, #c026d3, #ec4899); }
</style>
