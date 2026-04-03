<template>
  <div>
    <div class="admin-page-header">
      <div>
        <h2>{{ isEdit ? "Edit Prompt" : "New Prompt" }}</h2>
        <p class="muted" v-if="isEdit">ID: {{ route.params.id }}</p>
      </div>
      <RouterLink class="btn secondary" to="/admin/prompts">← Back to list</RouterLink>
    </div>

    <div v-if="loading" class="muted">Loading...</div>
    <div v-else-if="loadError" class="error-msg">{{ loadError }}</div>

    <form v-else @submit.prevent="save" class="admin-form">
      <!-- Kind -->
      <div class="form-row">
        <label class="form-label">Kind *</label>
        <div class="radio-group">
          <label class="radio-label">
            <input type="radio" v-model="form.kind" value="grammar" /> Grammar
          </label>
          <label class="radio-label">
            <input type="radio" v-model="form.kind" value="vocab" /> Vocab
          </label>
        </div>
      </div>

      <!-- Grammar point selector -->
      <div class="form-row" v-if="form.kind === 'grammar'">
        <label class="form-label">Grammar point</label>
        <select v-model="form.grammar_point_id" class="form-input">
          <option :value="null">— None —</option>
          <option v-for="gp in grammarPoints" :key="gp.id" :value="gp.id">
            [{{ gp.level }}] {{ gp.title }}
          </option>
        </select>
      </div>

      <!-- Vocab item selector -->
      <div class="form-row" v-if="form.kind === 'vocab'">
        <label class="form-label">Vocab item</label>
        <select v-model="form.vocab_item_id" class="form-input">
          <option :value="null">— None —</option>
          <option v-for="vi in vocabItems" :key="vi.id" :value="vi.id">
            [{{ vi.level }}] {{ vi.word }} — {{ vi.translation }}
          </option>
        </select>
      </div>

      <!-- Sentence -->
      <div class="form-row">
        <label class="form-label">Sentence * <span class="form-hint-inline">(use <code>___</code> for the blank)</span></label>
        <input v-model="form.sentence" class="form-input" required placeholder="Ella ___ de Madrid." />
        <div v-if="form.sentence" class="sentence-preview">
          Preview: <span v-html="highlightBlank(form.sentence)"></span>
        </div>
      </div>

      <!-- Answers -->
      <div class="form-row">
        <label class="form-label">Accepted answers * <span class="form-hint-inline">(at least one required)</span></label>
        <div class="answers-list">
          <div v-for="(ans, i) in form.answers" :key="i" class="answer-row">
            <input v-model="form.answers[i]" class="form-input answer-input" required placeholder="Answer…" />
            <button type="button" class="btn danger small" @click="removeAnswer(i)" :disabled="form.answers.length === 1">✕</button>
          </div>
        </div>
        <button type="button" class="btn secondary small" @click="addAnswer" style="margin-top:6px;">+ Add answer</button>
        <span class="form-hint">Multiple answers handle spelling variants, e.g. "es" and "está".</span>
      </div>

      <!-- Notes -->
      <div class="form-row">
        <label class="form-label">Notes</label>
        <textarea v-model="form.notes" class="form-input" rows="2"></textarea>
      </div>

      <div v-if="saveError" class="error-msg">{{ saveError }}</div>

      <div class="form-actions">
        <button type="submit" class="btn" :disabled="saving">
          {{ saving ? "Saving…" : (isEdit ? "Save changes" : "Create prompt") }}
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

const loading = ref(false);
const loadError = ref(null);
const saving = ref(false);
const saveError = ref(null);
const grammarPoints = ref([]);
const vocabItems = ref([]);

const form = reactive({
  kind: "grammar",
  grammar_point_id: null,
  vocab_item_id: null,
  sentence: "",
  notes: "",
  answers: [""],
});

function highlightBlank(s) {
  return s.replace(/___/g, '<span class="blank">___</span>');
}

function addAnswer() { form.answers.push(""); }
function removeAnswer(i) { form.answers.splice(i, 1); }

function buildPayload() {
  return {
    kind: form.kind,
    grammar_point_id: form.kind === "grammar" ? form.grammar_point_id : null,
    vocab_item_id: form.kind === "vocab" ? form.vocab_item_id : null,
    sentence: form.sentence,
    notes: form.notes || null,
    answers: form.answers.map(a => a.trim()).filter(Boolean),
  };
}

async function save() {
  saving.value = true;
  saveError.value = null;
  try {
    const payload = buildPayload();
    if (isEdit.value) {
      await apiFetch(`/api/admin/prompts/${route.params.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      await apiFetch("/api/admin/prompts", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    router.push("/admin/prompts");
  } catch (e) {
    saveError.value = e.detail?.detail || JSON.stringify(e.detail) || e.message;
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  loading.value = true;
  try {
    // Load grammar points and vocab items for selectors
    const [gpData, viData] = await Promise.all([
      apiFetch("/api/admin/grammar-points"),
      apiFetch("/api/admin/vocab-items"),
    ]);
    grammarPoints.value = gpData.items;
    vocabItems.value = viData.items;

    if (isEdit.value) {
      const data = await apiFetch(`/api/admin/prompts/${route.params.id}`);
      form.kind = data.kind;
      form.grammar_point_id = data.grammar_point_id;
      form.vocab_item_id = data.vocab_item_id;
      form.sentence = data.sentence;
      form.notes = data.notes || "";
      form.answers = data.answers.length ? [...data.answers] : [""];
    }
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
.form-hint-inline { font-size: 12px; color: var(--text-muted); font-weight: normal; }
.form-input {
  width: 100%; padding: 8px 10px; border: 1px solid var(--border-color);
  border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary);
  font-size: 14px; box-sizing: border-box;
}
.form-input:focus { outline: none; border-color: var(--accent); }
textarea.form-input { resize: vertical; font-family: inherit; }
.form-hint { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: block; }

.radio-group { display: flex; gap: 20px; }
.radio-label { display: flex; align-items: center; gap: 6px; font-size: 14px; cursor: pointer; }

.sentence-preview {
  margin-top: 6px; font-size: 14px; padding: 8px 10px;
  background: var(--bg-tertiary); border-radius: 6px;
}
:deep(.blank) { font-weight: 700; color: var(--accent); }

.answers-list { display: flex; flex-direction: column; gap: 6px; }
.answer-row { display: flex; gap: 6px; align-items: center; }
.answer-input { flex: 1; width: auto; }

.error-msg { color: var(--error); font-size: 14px; margin: 8px 0; }
.form-actions { margin-top: 24px; }
.btn.small { padding: 4px 10px; font-size: 12px; }
.btn.danger { background: var(--error); color: #fff; border-color: var(--error); }
code { font-family: monospace; background: var(--bg-tertiary); padding: 1px 4px; border-radius: 3px; }
</style>
