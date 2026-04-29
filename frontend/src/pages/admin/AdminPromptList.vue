<template>
  <div>
    <div class="admin-page-header">
      <div>
        <h2>Prompts</h2>
        <p class="muted">{{ filtered.length }} shown</p>
      </div>
      <RouterLink class="btn" to="/admin/prompts/new">+ New Prompt</RouterLink>
    </div>

    <div class="filter-bar">
      <input v-model="search" class="search-input" placeholder="Filter by sentence…" />
      <select v-model="kindFilter" class="filter-select">
        <option value="">All kinds</option>
        <option value="grammar">Grammar</option>
        <option value="vocab">Vocab</option>
      </select>
    </div>

    <div v-if="loading" class="muted">Loading...</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <div v-else class="admin-table-wrap">
      <div v-if="actionError" class="error-msg" role="alert">{{ actionError }}</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Kind</th>
            <th>Sentence</th>
            <th>Linked to</th>
            <th>Answers</th>
            <th style="text-align:right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filtered" :key="p.id">
            <td><span class="kind-chip" :class="p.kind">{{ p.kind }}</span></td>
            <td class="sentence-cell">
              <span v-html="highlightBlank(p.sentence)"></span>
            </td>
            <td class="muted ref-cell">
              <span v-if="p.grammar_point_title" class="ref-label">
                <Icon name="book" />
                {{ p.grammar_point_title }}
              </span>
              <span v-else-if="p.vocab_item_word" class="ref-label">
                <Icon name="tag" />
                {{ p.vocab_item_word }}
              </span>
              <span v-else>—</span>
            </td>
            <td>
              <span v-for="a in p.answers" :key="a" class="answer-chip">{{ a }}</span>
            </td>
            <td>
              <div class="row-actions">
                <RouterLink class="btn secondary small" :to="`/admin/prompts/${p.id}/edit`">Edit</RouterLink>
                <button class="btn danger small" @click="confirmDelete(p)" :disabled="deleting === p.id">
                  {{ deleting === p.id ? '…' : 'Delete' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!filtered.length" class="muted" style="text-align:center; padding:20px;">No prompts match.</p>
    </div>

    <div v-if="pendingDelete" class="confirm-overlay" @click.self="pendingDelete = null">
      <div class="confirm-dialog">
        <h3>Delete this prompt?</h3>
        <p class="mono muted">{{ pendingDelete.sentence }}</p>
        <p class="muted">This cannot be undone.</p>
        <div class="confirm-actions">
          <button class="btn secondary" @click="pendingDelete = null">Cancel</button>
          <button class="btn danger" @click="doDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { apiFetch } from "../../api";
import Icon from "../../components/Icon.vue";

const items = ref([]);
const loading = ref(true);
const error = ref(null);
const actionError = ref(null);
const deleting = ref(null);
const pendingDelete = ref(null);
const search = ref("");
const kindFilter = ref("");

const filtered = computed(() => {
  let list = items.value;
  if (kindFilter.value) list = list.filter(p => p.kind === kindFilter.value);
  if (search.value) {
    const q = search.value.toLowerCase();
    list = list.filter(p => p.sentence.toLowerCase().includes(q));
  }
  return list;
});

function highlightBlank(sentence) {
  return sentence.replace(/___/g, '<span class="blank">___</span>');
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const data = await apiFetch("/api/admin/prompts");
    items.value = data.items;
  } catch (e) {
    error.value = e.detail?.detail || e.message;
  } finally {
    loading.value = false;
  }
}

function confirmDelete(p) {
  actionError.value = null;
  pendingDelete.value = p;
}

async function doDelete() {
  const p = pendingDelete.value;
  pendingDelete.value = null;
  deleting.value = p.id;
  actionError.value = null;
  try {
    await apiFetch(`/api/admin/prompts/${p.id}`, { method: "DELETE" });
    items.value = items.value.filter(x => x.id !== p.id);
  } catch (e) {
    actionError.value = e.detail?.detail || "Failed to delete";
  } finally {
    deleting.value = null;
  }
}

onMounted(load);
</script>

<style scoped>
.admin-page-header {
  display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;
}
.admin-page-header h2 { margin: 0; }
.filter-bar { display: flex; gap: 10px; margin-bottom: 16px; }
.search-input {
  flex: 1; padding: 7px 10px; border: 1px solid var(--border-color);
  border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary); font-size: 14px;
}
.search-input:focus { outline: none; border-color: var(--accent); }
.filter-select {
  padding: 7px 10px; border: 1px solid var(--border-color);
  border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary); font-size: 14px;
}
.admin-table-wrap { overflow-x: auto; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.admin-table th {
  text-align: left; padding: 8px 12px;
  border-bottom: 1px solid var(--border-color); color: var(--text-muted); font-weight: 500;
}
.admin-table td { padding: 10px 12px; border-bottom: 1px solid var(--border-color); vertical-align: middle; }
.admin-table tr:last-child td { border-bottom: none; }

.kind-chip {
  display: inline-block; padding: 2px 7px; border-radius: 4px;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
}
.kind-chip.grammar { background: rgba(96, 165, 250, 0.15); color: var(--accent); }
.kind-chip.vocab { background: rgba(34, 197, 94, 0.15); color: var(--success); }

.sentence-cell { font-size: 13px; max-width: 300px; }
:deep(.blank) { font-weight: 700; color: var(--accent); }

.ref-cell { font-size: 13px; max-width: 180px; }
.ref-label {
  display: inline-flex; align-items: center; gap: 5px;
}
.ref-label svg { width: 13px; height: 13px; flex-shrink: 0; }

.answer-chip {
  display: inline-block; padding: 1px 6px; margin: 1px 2px;
  border-radius: 4px; background: var(--bg-tertiary);
  font-size: 12px; color: var(--text-muted);
}

.row-actions { display: flex; gap: 6px; justify-content: flex-end; }
.btn.small { padding: 4px 10px; font-size: 12px; }
.btn.danger { background: var(--error); color: #fff; border-color: var(--error); }
.error-msg { color: var(--error); padding: 12px 0; }
.mono { font-family: monospace; font-size: 13px; }

.confirm-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.confirm-dialog {
  background: var(--bg-secondary); border: 1px solid var(--border-color);
  border-radius: 10px; padding: 24px; max-width: 420px; width: 90%;
}
.confirm-dialog h3 { margin: 0 0 8px; }
.confirm-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
</style>
