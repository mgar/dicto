<template>
  <div v-if="item" class="grammar-detail">
    <!-- Header -->
    <div class="header">
      <RouterLink class="back-link" to="/grammar">
        <Icon name="chevron-left" class="back-icon" />
        Back to Grammar
      </RouterLink>
      
      <div class="title-row">
        <div class="pill">{{ item.level }}</div>
        <h1>{{ item.title }}</h1>
      </div>
      <p class="subtitle">{{ item.short_description }}</p>
      <div v-if="item.mastery" class="mastery-row">
        <span class="mastery-chip">{{ item.mastery.label }}</span>
        <span class="mastery-meta">
          {{ item.mastery.reviewed_prompts }}/{{ item.mastery.total_prompts }} prompts reviewed
        </span>
      </div>
    </div>

    <!-- Main content grid -->
    <div class="content-grid">
      <!-- Structure card -->
      <div class="card structure-card" v-if="item.structure && item.structure.length > 0">
        <h3>
          <Icon name="list" class="section-icon" />
          Structure
        </h3>
        <div class="structure-list">
          <div v-for="(pattern, idx) in item.structure" :key="idx" class="structure-item">
            <span class="structure-pattern" v-html="formatStructure(pattern)"></span>
          </div>
        </div>
      </div>

      <!-- Explanation card -->
      <div class="card explanation-card">
        <h3>
          <Icon name="info" class="section-icon" />
          About {{ item.title }}
        </h3>
        <div class="explanation-content" v-html="formatExplanation(item.explanation)"></div>
      </div>
    </div>

    <!-- Examples section -->
    <div class="examples-section" v-if="item.examples && item.examples.length > 0">
      <h3>
        <Icon name="chat" class="section-icon" />
        Examples
      </h3>
      
      <div class="examples-list">
        <div v-for="example in item.examples" :key="example.id" class="example-card">
          <div class="example-spanish" v-html="highlightText(example.sentence, example.highlight)"></div>
          <div class="example-english">{{ example.translation }}</div>
          <div v-if="example.notes" class="example-notes">{{ example.notes }}</div>
        </div>
      </div>
    </div>

    <!-- Practice button -->
    <div class="actions">
      <RouterLink class="btn" to="/learn">
        Practice this Grammar
      </RouterLink>
    </div>
  </div>

  <div v-else class="loading">
    Loading...
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import Icon from "../components/Icon.vue";
import { useRoute } from "vue-router";
import { apiFetch } from "../api";

const route = useRoute();
const item = ref(null);

onMounted(async () => {
  const data = await apiFetch(`/api/grammar-points/${route.params.id}`);
  item.value = data;
});

function formatStructure(pattern) {
  // Highlight keywords in structure patterns
  return pattern
    .replace(/\b(ser|estar|el|la|los|las)\b/gi, '<span class="keyword">$1</span>')
    .replace(/\+/g, '<span class="plus">+</span>');
}

function formatExplanation(text) {
  if (!text) return '';
  
  // Convert markdown-like formatting to HTML
  let html = text
    // Bold: **text**
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Lists starting with -
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    // Wrap consecutive <li> in <ul>
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  
  // Clean up newlines inside <ul> tags (they cause extra spacing)
  html = html.replace(/<ul>([\s\S]*?)<\/ul>/g, (match, content) => {
    return '<ul>' + content.replace(/\n/g, '') + '</ul>';
  });
  
  // Split by double newlines for paragraphs
  html = html
    .split('\n\n')
    .map(p => p.trim())
    .filter(p => p)
    .map(p => p.startsWith('<ul>') ? p : `<p>${p}</p>`)
    .join('');
  
  return html;
}

function highlightText(sentence, highlight) {
  if (!highlight) return sentence;
  
  const words = highlight.split(',').map(w => w.trim());
  let result = sentence;
  
  words.forEach(word => {
    // Escape special regex characters
    const escapedWord = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    // Use Unicode-aware word boundaries (\p{L} matches any letter including accented)
    const regex = new RegExp(`(^|[^\\p{L}])(${escapedWord})(?=[^\\p{L}]|$)`, 'giu');
    result = result.replace(regex, '$1<mark>$2</mark>');
  });
  
  return result;
}
</script>

<style scoped>
.grammar-detail {
  max-width: 900px;
  margin: 0 auto;
}

.header {
  margin-bottom: 24px;
}

h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
}

.subtitle {
  color: var(--text-muted);
  font-size: 18px;
  margin: 0;
}

.content-grid {
  grid-template-columns: 1fr 2fr;
}

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
}

h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.structure-card {
  height: fit-content;
}

.structure-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.structure-item {
  padding: 10px 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  font-family: "JetBrains Mono", "Fira Code", monospace;
  font-size: 14px;
}

.structure-item :deep(.keyword) {
  color: var(--accent);
  font-weight: 600;
}

.structure-item :deep(.plus) {
  color: var(--text-muted);
  margin: 0 4px;
}

.explanation-card {
  min-height: 200px;
}

.explanation-content {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
}

.explanation-content :deep(strong) {
  color: var(--accent);
  font-weight: 600;
}

.explanation-content :deep(ul) {
  margin: 8px 0;
  padding-left: 20px;
}

.explanation-content :deep(li) {
  margin: 2px 0;
  line-height: 1.5;
}

.explanation-content :deep(p) {
  margin: 0 0 8px 0;
}

.explanation-content :deep(p:last-child) {
  margin-bottom: 0;
}

.examples-section {
  margin-bottom: 24px;
}

.examples-section > h3 {
  margin-bottom: 16px;
}

.examples-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.example-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px 20px;
  transition: border-color 0.2s;
}

.example-card:hover {
  border-color: var(--accent);
}

.actions {
  display: flex;
  gap: 12px;
}

.loading {
  text-align: center;
  padding: 60px;
  color: var(--text-muted);
}
</style>
