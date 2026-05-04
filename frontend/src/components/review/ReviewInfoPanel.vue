<template>
  <section class="review-info-panel surface" aria-label="Review item information">
    <div class="info-header">
      <div>
        <span class="info-eyebrow">{{ item.kind === "grammar" ? "Grammar Info" : "Vocabulary Info" }}</span>
        <h3 class="info-title">{{ title }}</h3>
        <p v-if="subtitle" class="info-subtitle">{{ subtitle }}</p>
      </div>
      <LevelBadge v-if="level" :level="level" size="small" />
    </div>

    <div v-if="loading" class="info-state">Loading info...</div>
    <div v-else-if="error" class="info-state error">{{ error }}</div>

    <template v-else-if="detail">
      <div v-if="item.kind === 'grammar'" class="info-grid">
        <div v-if="detail.structure?.length" class="info-card">
          <h4 class="info-section-title">Structure</h4>
          <div class="structure-list">
            <div v-for="(pattern, index) in detail.structure" :key="index" class="structure-item">
              {{ pattern }}
            </div>
          </div>
        </div>

        <div class="info-card">
          <h4 class="info-section-title">Details</h4>
          <p class="info-copy">{{ detail.short_description }}</p>
        </div>
      </div>

      <div v-if="item.kind === 'grammar' && detail.explanation" class="info-card full">
        <h4 class="info-section-title">Explanation</h4>
        <div class="info-copy rich-copy" v-html="formatExplanation(detail.explanation)"></div>
      </div>

      <div v-if="item.kind === 'grammar' && detail.examples?.length" class="info-card full">
        <h4 class="info-section-title">Examples</h4>
        <div class="example-list">
          <div v-for="example in detail.examples" :key="example.id" class="example-item">
            <div class="example-main">{{ example.sentence }}</div>
            <div class="example-translation">{{ example.translation }}</div>
            <div v-if="example.notes" class="example-notes">{{ example.notes }}</div>
          </div>
        </div>
      </div>

      <div v-if="item.kind === 'vocab'" class="info-grid">
        <div class="info-card">
          <h4 class="info-section-title">Meaning</h4>
          <p class="vocab-translation">{{ detail.translation }}</p>
          <p class="info-copy">
            <span v-if="detail.part_of_speech">{{ detail.part_of_speech }}</span>
            <span v-if="detail.gender"> · {{ detail.gender }}</span>
          </p>
        </div>

        <div v-if="detail.example_sentence" class="info-card">
          <h4 class="info-section-title">Example</h4>
          <div class="example-main">{{ detail.example_sentence }}</div>
          <div class="example-translation">{{ detail.example_translation }}</div>
        </div>
      </div>

      <div v-if="item.kind === 'vocab' && detail.notes" class="info-card full">
        <h4 class="info-section-title">Notes</h4>
        <p class="info-copy">{{ detail.notes }}</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed } from "vue";
import LevelBadge from "../badges/LevelBadge.vue";

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  detail: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
});

const title = computed(() => {
  if (props.item.kind === "grammar") {
    return props.detail?.title || props.item.grammar_title;
  }
  return props.detail?.word || props.item.vocab_word;
});

const subtitle = computed(() => {
  if (props.item.kind === "grammar") {
    return props.detail?.short_description;
  }
  return props.detail?.translation || props.item.vocab_translation;
});

const level = computed(() => {
  if (props.item.kind === "grammar") {
    return props.detail?.level;
  }
  return props.detail?.level || props.item.vocab_level;
});

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatExplanation(text) {
  if (!text) return "";

  const escaped = escapeHtml(text);
  let html = escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");

  html = html.replace(/<ul>([\s\S]*?)<\/ul>/g, (_match, content) => {
    return "<ul>" + content.replace(/\n/g, "") + "</ul>";
  });

  return html
    .split("\n\n")
    .map(paragraph => paragraph.trim())
    .filter(Boolean)
    .map(paragraph => paragraph.startsWith("<ul>") ? paragraph : `<p>${paragraph}</p>`)
    .join("");
}
</script>

<style scoped>
.review-info-panel {
  margin-top: 24px;
  padding: 24px;
  border-radius: 18px;
  scroll-margin-top: 24px;
}

.info-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.info-eyebrow {
  display: block;
  margin-bottom: 5px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.info-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.info-subtitle {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 14px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.info-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px;
}

.info-card.full {
  margin-top: 14px;
}

.info-section-title {
  margin: 0 0 10px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.structure-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.structure-item {
  padding: 10px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-family: "JetBrains Mono", "Fira Code", monospace;
  font-size: 13px;
}

.info-copy {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.65;
}

.rich-copy :deep(p) {
  margin: 0 0 12px;
}

.rich-copy :deep(p:last-child) {
  margin-bottom: 0;
}

.rich-copy :deep(strong) {
  color: var(--accent);
  font-weight: 800;
}

.rich-copy :deep(ul) {
  margin: 10px 0;
  padding-left: 20px;
}

.rich-copy :deep(li) {
  margin: 5px 0;
}

.example-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.example-item {
  padding: 12px 14px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.example-main {
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;
}

.example-translation,
.example-notes {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.5;
}

.example-notes {
  font-style: italic;
}

.vocab-translation {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.info-state {
  padding: 24px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  text-align: center;
}

.info-state.error {
  border-color: var(--error-border);
  color: var(--error);
  background: var(--error-tint);
}

@media (max-width: 640px) {
  .review-info-panel {
    padding: 18px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .info-title {
    font-size: 21px;
  }
}
</style>
