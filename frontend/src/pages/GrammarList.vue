<template>
  <div>
    <div class="page-header">
      <div>
        <h2>Grammar Points</h2>
        <p class="muted">Select grammar points to add to your learning queue</p>
      </div>

      <div class="actions">
        <button 
          v-if="selectedGrammarPoints.size > 0" 
          class="btn"
          @click="startLearning"
          :disabled="adding"
        >
          {{ adding ? 'Adding...' : `Start Learning (${selectedGrammarPoints.size})` }}
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
            <span class="level-count">{{ levelGroup.items.length }} grammar points</span>
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

        <!-- Grammar points in this level -->
        <div v-if="expandedLevels[levelGroup.level]" class="level-content">
          <div 
            v-for="gp in levelGroup.items" 
            :key="gp.id" 
            class="list-item"
          >
            <RouterLink :to="`/grammar/${gp.id}`" class="list-item-link">
              <div class="list-item-info">
                <h4>{{ gp.title }}</h4>
                <p class="muted">{{ gp.short_description }}</p>
              </div>
            </RouterLink>
            
            <div class="list-item-actions">
              <span class="prompts-count" :class="{ complete: gp.fully_added }">
                {{ gp.in_queue }}/{{ gp.total_prompts }}
              </span>
              <button 
                v-if="!gp.fully_added"
                class="checkbox-btn"
                :class="{ selected: selectedGrammarPoints.has(gp.id) }"
                @click="toggleGrammarPoint(gp.id)"
                :title="selectedGrammarPoints.has(gp.id) ? 'Deselect' : 'Select'"
              >
                <Icon v-if="selectedGrammarPoints.has(gp.id)" name="check" />
              </button>
              <span v-else class="added-badge" title="Already added">
                <Icon name="check" />
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state for levels with no grammar points -->
      <div v-if="levels.length === 0" class="empty-state">
        <p>No grammar points available yet.</p>
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
const selectedGrammarPoints = ref(new Set());
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

function toggleGrammarPoint(gpId) {
  if (selectedGrammarPoints.value.has(gpId)) {
    selectedGrammarPoints.value.delete(gpId);
  } else {
    selectedGrammarPoints.value.add(gpId);
  }
  // Force reactivity
  selectedGrammarPoints.value = new Set(selectedGrammarPoints.value);
}

function isLevelFullySelected(levelGroup) {
  const availableItems = levelGroup.items.filter(gp => !gp.fully_added);
  if (availableItems.length === 0) return false;
  return availableItems.every(gp => selectedGrammarPoints.value.has(gp.id));
}

function toggleLevelSelection(levelGroup) {
  const availableItems = levelGroup.items.filter(gp => !gp.fully_added);
  const allSelected = isLevelFullySelected(levelGroup);
  
  if (allSelected) {
    // Deselect all
    availableItems.forEach(gp => selectedGrammarPoints.value.delete(gp.id));
  } else {
    // Select all
    availableItems.forEach(gp => selectedGrammarPoints.value.add(gp.id));
  }
  // Force reactivity
  selectedGrammarPoints.value = new Set(selectedGrammarPoints.value);
}

async function startLearning() {
  if (selectedGrammarPoints.value.size === 0 || adding.value) return;
  
  adding.value = true;
  try {
    const timezoneParams = timezoneQuery();
    // Add all selected grammar points
    for (const gpId of selectedGrammarPoints.value) {
      await apiFetch(
        `/api/learn/add-grammar-point/${gpId}?${timezoneParams}`,
        { method: "POST" }
      );
    }
    
    // Clear selection
    selectedGrammarPoints.value.clear();
    
    // Refresh data
    await loadData();
    await counts.refresh();
  } catch (e) {
    console.error("Failed to add grammar points:", e);
  } finally {
    adding.value = false;
  }
}

async function loadData() {
  const data = await apiFetch("/api/grammar-points/by-level");
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
</style>
