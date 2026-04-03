<template>
  <div>
    <div class="admin-page-header">
      <div>
        <h2>{{ isEdit ? "Edit Vocab Item" : "New Vocab Item" }}</h2>
        <p class="muted" v-if="isEdit">ID: {{ route.params.id }}</p>
      </div>
      <RouterLink class="btn secondary" to="/admin/vocab">← Back to list</RouterLink>
    </div>

    <div v-if="loading" class="muted">Loading...</div>
    <div v-else-if="loadError" class="error-msg">{{ loadError }}</div>

    <form v-else @submit.prevent="save" class="admin-form">
      <div class="form-row two-col">
        <div>
          <label class="form-label">Word *</label>
          <input v-model="form.word" class="form-input" required />
        </div>
        <div>
          <label class="form-label">Translation *</label>
          <input v-model="form.translation" class="form-input" required />
        </div>
      </div>

      <div class="form-row three-col">
        <div>
          <label class="form-label">Level *</label>
          <select v-model="form.level" class="form-input" required>
            <option v-for="l in levels" :key="l" :value="l">{{ l }}</option>
          </select>
        </div>
        <div>
          <label class="form-label">Part of speech</label>
          <select v-model="form.part_of_speech" class="form-input">
            <option value="">—</option>
            <option v-for="p in partsOfSpeech" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
        <div>
          <label class="form-label">Gender</label>
          <select v-model="form.gender" class="form-input">
            <option value="">—</option>
            <option value="m">m (masculine)</option>
            <option value="f">f (feminine)</option>
            <option value="n">n (neutral)</option>
          </select>
        </div>
      </div>

      <div class="form-row two-col">
        <div>
          <label class="form-label">Example sentence</label>
          <input v-model="form.example_sentence" class="form-input" placeholder="Ella ___ come mucho." />
        </div>
        <div>
          <label class="form-label">Example translation</label>
          <input v-model="form.example_translation" class="form-input" />
        </div>
      </div>

      <div class="form-row">
        <label class="form-label">Notes</label>
        <textarea v-model="form.notes" class="form-input" rows="2"></textarea>
      </div>

      <div class="form-row">
        <label class="form-label">Tags</label>
        <input v-model="form.tags" class="form-input" placeholder="food,kitchen,daily" />
        <span class="form-hint">Comma-separated, e.g. "food,kitchen,daily"</span>
      </div>

      <div v-if="saveError" class="error-msg">{{ saveError }}</div>

      <div class="form-actions">
        <button type="submit" class="btn" :disabled="saving">
          {{ saving ? "Saving…" : (isEdit ? "Save changes" : "Create vocab item") }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiFetch } from "../../api";

const route = useRoute();
const router = useRouter();
const isEdit = computed(() => !!route.params.id);

const levels = ["A1", "A2", "B1", "B2", "C1", "C2"];
const partsOfSpeech = ["noun", "verb", "adjective", "adverb", "pronoun", "preposition", "conjunction", "interjection", "article"];

const loading = ref(false);
const loadError = ref(null);
const saving = ref(false);
const saveError = ref(null);

const form = reactive({
  level: "A1",
  word: "",
  translation: "",
  part_of_speech: "",
  gender: "",
  example_sentence: "",
  example_translation: "",
  notes: "",
  tags: "",
});

function buildPayload() {
  return {
    level: form.level,
    word: form.word,
    translation: form.translation,
    part_of_speech: form.part_of_speech || null,
    gender: form.gender || null,
    example_sentence: form.example_sentence || null,
    example_translation: form.example_translation || null,
    notes: form.notes || null,
    tags: form.tags || null,
  };
}

async function save() {
  saving.value = true;
  saveError.value = null;
  try {
    if (isEdit.value) {
      await apiFetch(`/api/admin/vocab-items/${route.params.id}`, {
        method: "PUT",
        body: JSON.stringify(buildPayload()),
      });
    } else {
      await apiFetch("/api/admin/vocab-items", {
        method: "POST",
        body: JSON.stringify(buildPayload()),
      });
    }
    router.push("/admin/vocab");
  } catch (e) {
    saveError.value = e.detail?.detail || JSON.stringify(e.detail) || e.message;
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  if (!isEdit.value) return;
  loading.value = true;
  try {
    const data = await apiFetch(`/api/admin/vocab-items/${route.params.id}`);
    Object.assign(form, {
      level: data.level,
      word: data.word,
      translation: data.translation,
      part_of_speech: data.part_of_speech || "",
      gender: data.gender || "",
      example_sentence: data.example_sentence || "",
      example_translation: data.example_translation || "",
      notes: data.notes || "",
      tags: data.tags || "",
    });
  } catch (e) {
    loadError.value = e.detail?.detail || e.message;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.admin-page-header {
  display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;
}
.admin-page-header h2 { margin: 0; }
.admin-form { max-width: 680px; }
.form-row { margin-bottom: 16px; }
.form-label { display: block; font-size: 13px; font-weight: 500; color: var(--text-muted); margin-bottom: 5px; }
.form-input {
  width: 100%; padding: 8px 10px; border: 1px solid var(--border-color);
  border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary);
  font-size: 14px; box-sizing: border-box;
}
.form-input:focus { outline: none; border-color: var(--accent); }
textarea.form-input { resize: vertical; font-family: inherit; }
.form-hint { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: block; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.error-msg { color: var(--error); font-size: 14px; margin: 8px 0; }
.form-actions { margin-top: 24px; }
</style>
