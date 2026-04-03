<template>
  <div v-if="item" class="vocab-detail">
    <!-- Header -->
    <div class="header">
      <RouterLink class="back-link" to="/vocab">
        <Icon name="chevron-left" class="back-icon" />
        Back to Vocabulary
      </RouterLink>
      
      <div class="title-row">
        <div class="pill">{{ item.level }}</div>
        <h1>{{ item.word }}</h1>
        <span v-if="item.gender" class="gender-badge">{{ genderLabel }}</span>
        <span v-if="item.part_of_speech" class="pos-badge">{{ item.part_of_speech }}</span>
      </div>
      <p class="translation">{{ item.translation }}</p>
      <div v-if="item.mastery" class="mastery-row">
        <span class="mastery-chip">{{ item.mastery.label }}</span>
        <span class="mastery-meta">
          {{ item.mastery.reviewed_prompts }}/{{ item.mastery.total_prompts }} prompts reviewed
        </span>
      </div>
    </div>

    <!-- Main content grid -->
    <div class="content-grid">
      <!-- Word info card -->
      <div class="card info-card">
        <h3>
          <Icon name="info" class="section-icon" />
          Word Information
        </h3>
        <div class="info-list">
          <div class="info-item">
            <span class="info-label">Translation</span>
            <span class="info-value">{{ item.translation }}</span>
          </div>
          <div v-if="item.part_of_speech" class="info-item">
            <span class="info-label">Part of Speech</span>
            <span class="info-value">{{ item.part_of_speech }}</span>
          </div>
          <div v-if="item.gender" class="info-item">
            <span class="info-label">Gender</span>
            <span class="info-value">{{ genderLabel }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Level</span>
            <span class="info-value">{{ item.level }} - {{ getLevelName(item.level) }}</span>
          </div>
          <div v-if="item.tags" class="info-item">
            <span class="info-label">Categories</span>
            <div class="tags-list">
              <span v-for="tag in parseTags(item.tags)" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Example card -->
      <div class="card example-card" v-if="item.example_sentence">
        <h3>
          <Icon name="chat" class="section-icon" />
          Example Sentence
        </h3>
        <div class="example-content">
          <p class="example-spanish" v-html="highlightWord(item.example_sentence, item.word)"></p>
          <p class="example-english">{{ item.example_translation }}</p>
        </div>
      </div>

      <!-- Notes card -->
      <div class="card notes-card" v-if="item.notes">
        <h3>
          <Icon name="file-text" class="section-icon" />
          Notes
        </h3>
        <p class="notes-content">{{ item.notes }}</p>
      </div>
    </div>

    <!-- Practice button -->
    <div class="actions">
      <RouterLink class="btn" to="/learn">
        Practice this Word
      </RouterLink>
    </div>
  </div>

  <div v-else class="loading">
    Loading...
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import Icon from "../components/Icon.vue";
import { useRoute } from "vue-router";
import { apiFetch } from "../api";

const route = useRoute();
const item = ref(null);

const levelNames = {
  A1: "Beginner",
  A2: "Elementary", 
  B1: "Intermediate",
  B2: "Upper Intermediate",
  C1: "Advanced",
  C2: "Mastery",
};

const genderLabel = computed(() => {
  if (!item.value || !item.value.gender) return '';
  const genders = {
    'm': 'Masculine',
    'f': 'Feminine',
    'n': 'Neutral',
  };
  return genders[item.value.gender] || item.value.gender;
});

function getLevelName(level) {
  return levelNames[level] || level;
}

function parseTags(tags) {
  if (!tags) return [];
  return tags.split(',').map(t => t.trim()).filter(Boolean);
}

function highlightWord(sentence, word) {
  if (!word || !sentence) return sentence;
  const regex = new RegExp(`\\b(${word})\\b`, 'gi');
  return sentence.replace(regex, '<mark>$1</mark>');
}

onMounted(async () => {
  const data = await apiFetch(`/api/vocab-items/${route.params.id}`);
  item.value = data;
});
</script>

<style scoped>
.vocab-detail {
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

.gender-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
  background: var(--accent-tint);
  color: var(--accent);
}

.pos-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-muted);
  border: 1px solid var(--border-color);
}

.translation {
  color: var(--text-muted);
  font-size: 20px;
  margin: 8px 0 0 0;
}

.content-grid {
  grid-template-columns: 1fr 1fr;
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

.info-card {
  height: fit-content;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 15px;
  color: var(--text-primary);
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 12px;
  padding: 4px 10px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-muted);
}

.example-content {
  padding: 16px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.example-english {
  margin: 0;
  font-style: italic;
}

.notes-card {
  grid-column: span 2;
}

@media (max-width: 768px) {
  .notes-card {
    grid-column: span 1;
  }
}

.notes-content {
  margin: 0;
  line-height: 1.6;
  color: var(--text-primary);
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
