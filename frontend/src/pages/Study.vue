<template>
  <div class="study-page">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading your lesson...</p>
    </div>

    <!-- No new items -->
    <div v-else-if="items.length === 0" class="empty-state">
      <div class="empty-icon">
        <Icon name="check-circle" stroke-width="1.5" />
      </div>
      <h2>Nothing new to learn</h2>
      <p class="muted">You've seen all your queued items. Add more content or start reviewing!</p>
      <div class="empty-actions">
        <RouterLink class="btn" to="/learn">Add More Content</RouterLink>
        <RouterLink class="btn secondary" to="/review">Start Review</RouterLink>
      </div>
    </div>

    <!-- Study content -->
    <div v-else class="study-container">
      <!-- Progress -->
      <div class="progress-header">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <div class="progress-info">
          <span class="progress-text">{{ currentIndex + 1 }} of {{ items.length }}</span>
          <span class="progress-label">new items</span>
        </div>
      </div>

      <!-- Grammar card -->
      <div v-if="currentItem.kind === 'grammar'" class="content-card card grammar-card">
        <div class="card-header">
          <TypeBadge type="grammar" />
          <LevelBadge :level="currentItem.grammar_level" />
        </div>
        
        <h1 class="card-title">{{ currentItem.grammar_title }}</h1>
        <p class="card-description">{{ currentItem.grammar_description }}</p>

        <!-- Structure -->
        <div v-if="currentItem.grammar_structure?.length" class="section structure-section">
          <h3>Structure</h3>
          <div class="structure-list">
            <div v-for="(pattern, idx) in currentItem.grammar_structure" :key="idx" class="structure-item">
              <span v-html="formatStructure(pattern)"></span>
            </div>
          </div>
        </div>

        <!-- Explanation -->
        <div v-if="currentItem.grammar_explanation" class="section explanation-section">
          <h3>Explanation</h3>
          <div class="explanation-text" v-html="formatExplanation(currentItem.grammar_explanation)"></div>
        </div>

        <!-- Examples -->
        <div v-if="currentItem.grammar_examples?.length" class="section examples-section">
          <h3>Examples</h3>
          <div class="examples-list">
            <div v-for="ex in currentItem.grammar_examples" :key="ex.id" class="example-item">
              <div class="example-spanish" v-html="highlightText(ex.sentence, ex.highlight)"></div>
              <div class="example-english">{{ ex.translation }}</div>
              <div v-if="ex.notes" class="example-notes">{{ ex.notes }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Vocab card -->
      <div v-else class="content-card card vocab-card">
        <div class="card-header">
          <TypeBadge type="vocab" />
          <LevelBadge :level="currentItem.vocab_level" />
        </div>

        <div class="vocab-main">
          <h1 class="vocab-word">{{ currentItem.vocab_word }}</h1>
          <div class="vocab-meta">
            <span v-if="currentItem.vocab_pos" class="pos">{{ currentItem.vocab_pos }}</span>
            <span v-if="currentItem.vocab_gender" class="gender">({{ currentItem.vocab_gender }})</span>
          </div>
          <p class="vocab-translation">{{ currentItem.vocab_translation }}</p>
        </div>

        <div v-if="currentItem.vocab_example" class="section example-section">
          <h3>Example</h3>
          <div class="example-item">
            <div class="example-spanish">{{ currentItem.vocab_example }}</div>
            <div class="example-english">{{ currentItem.vocab_example_translation }}</div>
          </div>
        </div>

        <div v-if="currentItem.vocab_notes" class="section notes-section">
          <h3>Notes</h3>
          <p>{{ currentItem.vocab_notes }}</p>
        </div>
      </div>

      <!-- Navigation -->
      <div class="nav-footer">
        <button 
          v-if="currentIndex > 0" 
          class="btn secondary lg" 
          :disabled="startingReview"
          @click="previous"
        >
          <Icon name="chevron-left" />
          Previous
        </button>
        <div v-else></div>

        <button 
          class="btn primary lg" 
          :disabled="startingReview"
          @click="next"
        >
          <span v-if="isLastItem">{{ startingReview ? 'Starting...' : 'Start Review' }}</span>
          <span v-else>Next</span>
          <Icon name="chevron-right" />
        </button>
      </div>

      <p v-if="studyError" class="study-error" role="alert">
        {{ studyError }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { apiFetch } from "../api";
import { useCounts } from "../counts";
import Icon from "../components/Icon.vue";
import LevelBadge from "../components/badges/LevelBadge.vue";
import TypeBadge from "../components/badges/TypeBadge.vue";

const router = useRouter();
const counts = useCounts();

const loading = ref(true);
const startingReview = ref(false);
const studyError = ref("");
const items = ref([]);
const currentIndex = ref(0);

const currentItem = computed(() => items.value[currentIndex.value] || {});
const isLastItem = computed(() => currentIndex.value === items.value.length - 1);
const progressPercent = computed(() => ((currentIndex.value + 1) / items.value.length) * 100);

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
  
  // Clean up newlines inside <ul> tags
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

async function loadNewItems() {
  loading.value = true;
  studyError.value = "";
  try {
    const data = await apiFetch("/api/learn/study-queue");
    items.value = data.items;
  } catch (e) {
    console.error("Failed to load study queue:", e);
  } finally {
    loading.value = false;
  }
}

function previous() {
  if (startingReview.value) return;
  if (currentIndex.value > 0) {
    currentIndex.value--;
  }
}

async function next() {
  if (startingReview.value) return;
  studyError.value = "";
  if (isLastItem.value) {
    // Mark items as "seen" and go to review
    startingReview.value = true;
    try {
      await apiFetch("/api/learn/mark-studied", { 
        method: "POST"
      });
      await counts.refresh();
      router.push("/review");
    } catch (e) {
      console.error("Failed to mark as studied:", e);
      studyError.value = "We couldn't start the review session. Please try again.";
    } finally {
      startingReview.value = false;
    }
  } else {
    currentIndex.value++;
  }
}

onMounted(loadNewItems);
</script>

<style scoped>
.study-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
  min-height: calc(100vh - 120px);
}

/* Progress header */
.progress-header {
  margin-bottom: 24px;
}

.progress-bar {
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: var(--blue-violet-gradient);
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-text {
  font-weight: 600;
  font-size: 18px;
}

.progress-label {
  color: var(--text-muted);
  font-size: 14px;
}

/* Content card */
.content-card {
  padding: 32px;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

/* Grammar card */
.card-title {
  font-size: 28px;
  margin: 0 0 8px;
  font-weight: 700;
}

.card-description {
  font-size: 16px;
  color: var(--text-muted);
  margin: 0 0 24px;
}

.section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.section h3 {
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin: 0 0 12px;
}

.structure-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.structure-item {
  padding: 12px 16px;
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

.explanation-text {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
}

.explanation-text :deep(p) {
  margin: 0 0 12px;
}

.explanation-text :deep(p:last-child) {
  margin-bottom: 0;
}

.explanation-text :deep(strong) {
  color: var(--accent);
  font-weight: 600;
}

.explanation-text :deep(ul) {
  margin: 8px 0;
  padding-left: 20px;
}

.explanation-text :deep(li) {
  margin: 4px 0;
  line-height: 1.6;
}

.examples-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.example-item {
  padding: 16px;
  background: var(--bg-primary);
  border-radius: 10px;
  border-left: 3px solid var(--accent);
}

.example-spanish {
  font-size: 17px;
  font-weight: 500;
  margin-bottom: 4px;
}

.example-english {
  font-size: 14px;
  color: var(--text-muted);
}

/* Vocab card */
.vocab-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px 0 30px;
}

.vocab-word {
  font-size: 42px;
  font-weight: 700;
  margin: 0 0 8px;
  background: var(--violet-blue-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: var(--transparent);
  background-clip: text;
}

.vocab-meta {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  color: var(--text-muted);
}

.pos {
  font-style: italic;
}

.vocab-translation {
  font-size: 24px;
  color: var(--text-primary);
  margin: 0;
}

.notes-section p {
  margin: 0;
  font-size: 14px;
  color: var(--text-muted);
  line-height: 1.6;
}

/* Navigation footer */
.nav-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
}

.study-error {
  margin: 14px 0 0;
  color: var(--error);
  font-size: 14px;
  font-weight: 600;
  text-align: right;
}

/* Mobile */
@media (max-width: 640px) {
  .content-card {
    padding: 24px 20px;
  }

  .card-title {
    font-size: 24px;
  }

  .vocab-word {
    font-size: 32px;
  }

  .vocab-translation {
    font-size: 20px;
  }
}
</style>
