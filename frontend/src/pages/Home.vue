<template>
  <section class="hero">
    <div class="hero-card surface">
      <div class="hero-eyebrow">
        <span class="pill subtle eyebrow-badge">
          <Icon name="book" />
          Spaced Repetition · Cloze Practice
        </span>
      </div>
      <h1>Learn Spanish.<br><span class="hero-accent">Master it completely.</span></h1>
      <p>
        Dicto focuses on deep mastery through cloze-based exercises and spaced repetition.
        Grammar and vocabulary, built for deliberate practice.
      </p>
      <div class="hero-actions">
        <RouterLink class="btn lg hero-btn" to="/login">Get started</RouterLink>
        <div class="hero-meta">
          <Icon name="check-circle" />
          No gamification. Just learning.
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import Icon from "../components/Icon.vue";
</script>

<style scoped>
.hero {
  padding: 48px 0 32px;
}

.hero-card {
  background: linear-gradient(145deg, var(--gradient-start) 0%, var(--gradient-end) 100%);
  border-radius: 20px;
  padding: 56px 48px;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s ease;
}

.hero-card::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 480px;
  height: 480px;
  background: radial-gradient(ellipse at top right, var(--hero-glow) 0%, var(--transparent) 65%);
  pointer-events: none;
}

[data-theme="light"] .hero-card::before {
  background: radial-gradient(ellipse at top right, var(--hero-glow) 0%, var(--transparent) 65%);
}

.hero-eyebrow {
  margin-bottom: 20px;
}

.eyebrow-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  letter-spacing: 0.01em;
}

.eyebrow-badge svg {
  width: 14px;
  height: 14px;
  color: var(--accent-light);
}

h1 {
  margin: 0 0 18px;
  font-size: 52px;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

.hero-accent {
  background: var(--accent-purple-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: var(--transparent);
  background-clip: text;
}

p {
  margin: 0 0 32px;
  color: var(--text-muted);
  max-width: 520px;
  font-size: 16.5px;
  line-height: 1.65;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13.5px;
  color: var(--text-muted);
}

.hero-meta svg {
  width: 16px;
  height: 16px;
  color: var(--success);
  flex-shrink: 0;
}

@media (max-width: 640px) {
  .hero-card {
    padding: 36px 24px;
  }

  h1 {
    font-size: 36px;
  }

  p {
    font-size: 15px;
  }

  .hero-actions {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }
}
</style>
