<template>
  <div>
    <div class="admin-page-header">
      <div>
        <h2>Vocab Items</h2>
        <p class="muted">{{ items.length }} total</p>
      </div>
      <RouterLink class="btn" to="/admin/vocab/new">+ New Vocab Item</RouterLink>
    </div>

    <div class="filter-bar">
      <input v-model="search" class="search-input" placeholder="Filter by word or translation…" />
      <select v-model="levelFilter" class="filter-select">
        <option value="">All levels</option>
        <option v-for="l in levels" :key="l" :value="l">{{ l }}</option>
      </select>
    </div>

    <div v-if="loading" class="muted">Loading...</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <div v-else class="admin-table-wrap">
      <div v-if="actionError" class="error-msg" role="alert">{{ actionError }}</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Level</th>
            <th>Word</th>
            <th>Translation</th>
            <th>POS / Gender</th>
            <th style="text-align:right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="vi in filtered" :key="vi.id">
            <td><span class="level-chip">{{ vi.level }}</span></td>
            <td class="word-cell">
              {{ vi.word }}
              <span v-if="vi.gender" class="gender-chip">{{ vi.gender }}</span>
            </td>
            <td>{{ vi.translation }}</td>
            <td class="muted">{{ vi.part_of_speech || '—' }}</td>
            <td>
              <div class="row-actions">
                <RouterLink class="btn secondary small" :to="`/admin/vocab/${vi.id}/edit`">Edit</RouterLink>
                <button class="btn danger small" @click="confirmDelete(vi)" :disabled="deleting === vi.id">
                  {{ deleting === vi.id ? '…' : 'Delete' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!filtered.length" class="muted" style="text-align:center; padding:20px;">No items match.</p>
    </div>

    <div v-if="pendingDelete" class="confirm-overlay" @click.self="pendingDelete = null">
      <div class="confirm-dialog">
        <h3>Delete "{{ pendingDelete.word }}"?</h3>
        <p class="muted">This will also delete all associated prompts. This cannot be undone.</p>
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

const items = ref([]);
const loading = ref(true);
const error = ref(null);
const actionError = ref(null);
const deleting = ref(null);
const pendingDelete = ref(null);
const search = ref("");
const levelFilter = ref("");
const levels = ["A1", "A2", "B1", "B2", "C1", "C2"];

const filtered = computed(() => {
  let list = items.value;
  if (levelFilter.value) list = list.filter(v => v.level === levelFilter.value);
  if (search.value) {
    const q = search.value.toLowerCase();
    list = list.filter(v =>
      v.word.toLowerCase().includes(q) || v.translation.toLowerCase().includes(q)
    );
  }
  return list;
});

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const data = await apiFetch("/api/admin/vocab-items");
    items.value = data.items;
  } catch (e) {
    error.value = e.detail?.detail || e.message;
  } finally {
    loading.value = false;
  }
}

function confirmDelete(vi) {
  actionError.value = null;
  pendingDelete.value = vi;
}

async function doDelete() {
  const vi = pendingDelete.value;
  pendingDelete.value = null;
  deleting.value = vi.id;
  actionError.value = null;
  try {
    await apiFetch(`/api/admin/vocab-items/${vi.id}`, { method: "DELETE" });
    items.value = items.value.filter(x => x.id !== vi.id);
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

.level-chip {
  display: inline-block; padding: 2px 7px; border-radius: 4px;
  font-size: 12px; font-weight: 600; background: var(--bg-tertiary); color: var(--accent);
}
.word-cell { display: flex; align-items: center; gap: 6px; }
.gender-chip {
  font-size: 11px; padding: 1px 5px; border-radius: 3px;
  background: var(--bg-tertiary); color: var(--text-muted);
}
.row-actions { display: flex; gap: 6px; justify-content: flex-end; }
.btn.small { padding: 4px 10px; font-size: 12px; }
.btn.danger { background: var(--error); color: #fff; border-color: var(--error); }
.error-msg { color: var(--error); padding: 12px 0; }

.confirm-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.confirm-dialog {
  background: var(--bg-secondary); border: 1px solid var(--border-color);
  border-radius: 10px; padding: 24px; max-width: 400px; width: 90%;
}
.confirm-dialog h3 { margin: 0 0 8px; }
.confirm-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
</style>
