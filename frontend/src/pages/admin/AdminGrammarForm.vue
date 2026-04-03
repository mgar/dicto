<template>
  <div>
    <div class="admin-page-header">
      <div>
        <h2>{{ isEdit ? "Edit Grammar Point" : "New Grammar Point" }}</h2>
        <p class="muted" v-if="isEdit">ID: {{ route.params.id }}</p>
      </div>
      <RouterLink class="btn secondary" to="/admin/grammar">← Back to list</RouterLink>
    </div>

    <div v-if="loading" class="muted">Loading...</div>
    <div v-else-if="loadError" class="error-msg">{{ loadError }}</div>

    <form v-else @submit.prevent="save" class="admin-form">
      <!-- Basic fields -->
      <div class="form-row">
        <label class="form-label">Level *</label>
        <select v-model="form.level" class="form-input" required>
          <option v-for="l in levels" :key="l" :value="l">{{ l }}</option>
        </select>
      </div>

      <div class="form-row">
        <label class="form-label">Title *</label>
        <input v-model="form.title" class="form-input" required @input="autoSlug" />
      </div>

      <div class="form-row">
        <label class="form-label">Slug *</label>
        <input v-model="form.slug" class="form-input" required pattern="[a-z0-9-]+" title="Lowercase letters, numbers, hyphens only" />
        <span class="form-hint">URL-safe identifier, e.g. "ser-estar-basics"</span>
      </div>

      <div class="form-row">
        <label class="form-label">Short description *</label>
        <input v-model="form.short_description" class="form-input" required maxlength="512" />
      </div>

      <div class="form-row">
        <label class="form-label">Structure patterns</label>
        <textarea v-model="form.structureText" class="form-input" rows="3" placeholder="One pattern per line, e.g.&#10;Noun + ser&#10;Adjective + ser"></textarea>
        <span class="form-hint">One pattern per line. Stored as JSON array.</span>
      </div>

      <div class="form-row">
        <label class="form-label">Explanation *</label>
        <textarea v-model="form.explanation" class="form-input" rows="6" required></textarea>
      </div>

      <!-- Examples -->
      <div class="section-header">
        <h3>Examples</h3>
        <button type="button" class="btn secondary small" @click="addExample">+ Add Example</button>
      </div>

      <div v-for="(ex, i) in form.examples" :key="i" class="example-card">
        <div class="example-header">
          <span class="example-num">Example {{ i + 1 }}</span>
          <button type="button" class="btn danger small" @click="removeExample(i)">Remove</button>
        </div>
        <div class="form-row">
          <label class="form-label">Sentence *</label>
          <input v-model="ex.sentence" class="form-input" required />
        </div>
        <div class="form-row">
          <label class="form-label">Translation *</label>
          <input v-model="ex.translation" class="form-input" required />
        </div>
        <div class="form-row two-col">
          <div>
            <label class="form-label">Highlight</label>
            <input v-model="ex.highlight" class="form-input" placeholder="Word(s) to highlight" />
          </div>
          <div>
            <label class="form-label">Sort order</label>
            <input v-model.number="ex.sort_order" class="form-input" type="number" min="0" />
          </div>
        </div>
        <div class="form-row">
          <label class="form-label">Notes</label>
          <input v-model="ex.notes" class="form-input" />
        </div>
      </div>

      <div v-if="saveError" class="error-msg">{{ saveError }}</div>

      <div class="form-actions">
        <button type="submit" class="btn" :disabled="saving">
          {{ saving ? "Saving…" : (isEdit ? "Save changes" : "Create grammar point") }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiFetch } from "../../api";

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const levels = ["A1", "A2", "B1", "B2", "C1", "C2"];

const loading = ref(false);
const loadError = ref(null);
const saving = ref(false);
const saveError = ref(null);

const form = reactive({
  level: "A1",
  title: "",
  slug: "",
  short_description: "",
  structureText: "",
  explanation: "",
  examples: [],
});

function autoSlug() {
  if (!isEdit.value) {
    form.slug = form.title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }
}

function addExample() {
  form.examples.push({ sentence: "", translation: "", highlight: "", notes: "", sort_order: form.examples.length });
}

function removeExample(i) {
  form.examples.splice(i, 1);
}

function buildPayload() {
  const structure = form.structureText
    .split("\n")
    .map(s => s.trim())
    .filter(Boolean);
  return {
    level: form.level,
    title: form.title,
    slug: form.slug,
    short_description: form.short_description,
    structure: structure.length ? structure : null,
    explanation: form.explanation,
    examples: form.examples.map(ex => ({
      sentence: ex.sentence,
      translation: ex.translation,
      highlight: ex.highlight || null,
      notes: ex.notes || null,
      sort_order: ex.sort_order ?? 0,
    })),
  };
}

async function save() {
  saving.value = true;
  saveError.value = null;
  try {
    const payload = buildPayload();
    if (isEdit.value) {
      await apiFetch(`/api/admin/grammar-points/${route.params.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      await apiFetch("/api/admin/grammar-points", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    router.push("/admin/grammar");
  } catch (e) {
    saveError.value = e.detail?.detail || JSON.stringify(e.detail) || e.message;
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  if (!isEdit.value) return;
  loading.value = true;
  loadError.value = null;
  try {
    const data = await apiFetch(`/api/admin/grammar-points/${route.params.id}`);
    form.level = data.level;
    form.title = data.title;
    form.slug = data.slug;
    form.short_description = data.short_description;
    form.structureText = (data.structure || []).join("\n");
    form.explanation = data.explanation;
    form.examples = (data.examples || []).map(ex => ({ ...ex }));
  } catch (e) {
    loadError.value = e.detail?.detail || e.message;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.admin-page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.admin-page-header h2 { margin: 0; }

.admin-form { max-width: 680px; }

.form-row { margin-bottom: 16px; }
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: 5px;
}
.form-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  box-sizing: border-box;
}
.form-input:focus { outline: none; border-color: var(--accent); }
textarea.form-input { resize: vertical; font-family: inherit; }
.form-hint { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: block; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 24px 0 12px;
  border-top: 1px solid var(--border-color);
  padding-top: 20px;
}
.section-header h3 { margin: 0; font-size: 15px; }

.example-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  background: var(--bg-secondary);
}
.example-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.example-num { font-size: 13px; font-weight: 600; color: var(--text-muted); }

.error-msg { color: var(--error); font-size: 14px; margin: 8px 0; }
.form-actions { margin-top: 24px; }

.btn.small { padding: 4px 10px; font-size: 12px; }
.btn.danger { background: var(--error); color: #fff; border-color: var(--error); }
</style>
