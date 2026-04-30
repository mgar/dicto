<template>
  <div>
    <div class="page-header">
      <div>
        <h2>Vocabulary</h2>
        <p class="muted">Select vocabulary to add to your learning queue</p>
      </div>

      <div class="actions">
        <button 
          v-if="selectedVocabItems.size > 0" 
          class="btn"
          @click="startLearning"
          :disabled="adding"
        >
          {{ adding ? 'Adding...' : `Start Learning (${selectedVocabItems.size})` }}
        </button>
        <RouterLink v-else class="btn secondary" to="/learn">
          Go to Learn
        </RouterLink>
      </div>
    </div>

    <div v-if="loading" class="loading-state">Loading...</div>

    <div v-else class="levels-list">
      <div v-for="levelGroup in levels" :key="levelGroup.level" class="level-section">
        <!-- Level header -->
        <div class="level-header" @click="toggleLevel(levelGroup.level)">
          <div class="level-title-row">
            <Icon name="chevron-right" class="chevron" :class="{ expanded: expandedLevels[levelGroup.level] }" />
            <LevelBadge :level="levelGroup.level" />
            <span class="level-name">{{ getLevelName(levelGroup.level) }}</span>
            <span class="level-count">{{ levelGroup.items.length }} words</span>
          </div>
          
          <div class="level-actions" @click.stop>
            <div class="progress-info">
              <span class="progress-text">{{ levelGroup.in_queue }} / {{ levelGroup.total_prompts }} in queue</span>
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: getProgressPercent(levelGroup) + '%' }"
                ></div>
              </div>
            </div>
            <button 
              class="btn secondary small"
              @click="toggleLevelSelection(levelGroup)"
              :disabled="levelGroup.in_queue >= levelGroup.total_prompts"
            >
              {{ isLevelFullySelected(levelGroup) ? 'Deselect All' : 'Select All' }}
            </button>
          </div>
        </div>

        <!-- Vocab items in this level -->
        <div v-if="expandedLevels[levelGroup.level]" class="level-content">
          <div 
            v-for="vi in levelGroup.items" 
            :key="vi.id" 
            class="list-item"
          >
            <RouterLink :to="`/vocab/${vi.id}`" class="list-item-link">
              <div class="list-item-info">
                <h4>
                  {{ vi.word }}
                  <span v-if="vi.gender" class="gender-badge">{{ vi.gender }}</span>
                  <span v-if="vi.part_of_speech" class="pos-badge">{{ vi.part_of_speech }}</span>
                </h4>
                <p class="muted">{{ vi.translation }}</p>
              </div>
            </RouterLink>
            
            <div class="list-item-actions">
              <span class="prompts-count" :class="{ complete: vi.fully_added }">
                {{ vi.in_queue }}/{{ vi.total_prompts }}
              </span>
              <button 
                v-if="!vi.fully_added"
                class="checkbox-btn"
                :class="{ selected: selectedVocabItems.has(vi.id) }"
                @click="toggleVocabItem(vi.id)"
                :title="selectedVocabItems.has(vi.id) ? 'Deselect' : 'Select'"
              >
                <Icon v-if="selectedVocabItems.has(vi.id)" name="check" />
              </button>
              <span v-else class="added-badge" title="Already added">
                <Icon name="check" />
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state for levels with no vocab items -->
      <div v-if="levels.length === 0" class="empty-state">
        <p>No vocabulary items available yet.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from "vue";
import { apiFetch, timezoneQuery } from "../api";
import { useCounts } from "../counts";
import LevelBadge from "../components/badges/LevelBadge.vue";
import Icon from "../components/Icon.vue";

const counts = useCounts();
const levels = ref([]);
const loading = ref(true);
const expandedLevels = reactive({});
const selectedVocabItems = ref(new Set());
const adding = ref(false);

const levelNames = {
  A1: "Beginner",
  A2: "Elementary", 
  B1: "Intermediate",
  B2: "Upper Intermediate",
  C1: "Advanced",
  C2: "Mastery",
};

function getLevelName(level) {
  return levelNames[level] || level;
}

function getProgressPercent(levelGroup) {
  if (levelGroup.total_prompts === 0) return 0;
  return Math.round((levelGroup.in_queue / levelGroup.total_prompts) * 100);
}

function toggleLevel(level) {
  expandedLevels[level] = !expandedLevels[level];
}

function toggleVocabItem(viId) {
  if (selectedVocabItems.value.has(viId)) {
    selectedVocabItems.value.delete(viId);
  } else {
    selectedVocabItems.value.add(viId);
  }
  // Force reactivity
  selectedVocabItems.value = new Set(selectedVocabItems.value);
}

function isLevelFullySelected(levelGroup) {
  const availableItems = levelGroup.items.filter(vi => !vi.fully_added);
  if (availableItems.length === 0) return false;
  return availableItems.every(vi => selectedVocabItems.value.has(vi.id));
}

function toggleLevelSelection(levelGroup) {
  const availableItems = levelGroup.items.filter(vi => !vi.fully_added);
  const allSelected = isLevelFullySelected(levelGroup);
  
  if (allSelected) {
    // Deselect all
    availableItems.forEach(vi => selectedVocabItems.value.delete(vi.id));
  } else {
    // Select all
    availableItems.forEach(vi => selectedVocabItems.value.add(vi.id));
  }
  // Force reactivity
  selectedVocabItems.value = new Set(selectedVocabItems.value);
}

async function startLearning() {
  if (selectedVocabItems.value.size === 0 || adding.value) return;
  
  adding.value = true;
  try {
    const timezoneParams = timezoneQuery();
    // Add all selected vocab items
    for (const viId of selectedVocabItems.value) {
      await apiFetch(
        `/api/learn/add-vocab-item/${viId}?${timezoneParams}`,
        { method: "POST" }
      );
    }
    
    // Clear selection
    selectedVocabItems.value.clear();
    
    // Refresh data
    await loadData();
    await counts.refresh();
  } catch (e) {
    console.error("Failed to add vocab items:", e);
  } finally {
    adding.value = false;
  }
}

async function loadData() {
  const data = await apiFetch("/api/vocab-items/by-level");
  levels.value = data.levels;
  
  // Expand first level by default if it has items
  if (data.levels.length > 0 && Object.keys(expandedLevels).length === 0) {
    expandedLevels[data.levels[0].level] = true;
  }
}

onMounted(async () => {
  await loadData();
  loading.value = false;
  counts.refresh();
});
</script>

<style scoped>
.actions {
  display: flex;
  gap: 10px;
}

.gender-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--accent-tint);
  color: var(--accent);
}

.pos-badge {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-muted);
}
</style>
