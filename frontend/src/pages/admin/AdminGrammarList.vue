<template>
  <div>
    <div class="admin-page-header">
      <div>
        <h2>Grammar Points</h2>
        <p class="muted">{{ items.length }} total</p>
      </div>
      <RouterLink class="btn" to="/admin/grammar/new">+ New Grammar Point</RouterLink>
    </div>

    <div v-if="loading" class="muted">Loading...</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <div v-else class="admin-table-wrap">
      <div v-if="actionError" class="error-msg" role="alert">{{ actionError }}</div>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Level</th>
            <th>Title</th>
            <th>Slug</th>
            <th style="text-align:right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="gp in items" :key="gp.id">
            <td><span class="level-chip">{{ gp.level }}</span></td>
            <td>
              <div class="item-title">{{ gp.title }}</div>
              <div class="item-sub muted">{{ gp.short_description }}</div>
            </td>
            <td class="mono muted">{{ gp.slug }}</td>
            <td>
              <div class="row-actions">
                <RouterLink class="btn secondary small" :to="`/admin/grammar/${gp.id}/edit`">Edit</RouterLink>
                <button class="btn danger small" @click="confirmDelete(gp)" :disabled="deleting === gp.id">
                  {{ deleting === gp.id ? '…' : 'Delete' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Confirm delete dialog -->
    <div v-if="pendingDelete" class="confirm-overlay" @click.self="pendingDelete = null">
      <div class="confirm-dialog">
        <h3>Delete "{{ pendingDelete.title }}"?</h3>
        <p class="muted">This will also delete all associated examples and prompts. This cannot be undone.</p>
        <div class="confirm-actions">
          <button class="btn secondary" @click="pendingDelete = null">Cancel</button>
          <button class="btn danger" @click="doDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { apiFetch } from "../../api";

const items = ref([]);
const loading = ref(true);
const error = ref(null);
const actionError = ref(null);
const deleting = ref(null);
const pendingDelete = ref(null);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const data = await apiFetch("/api/admin/grammar-points");
    items.value = data.items;
  } catch (e) {
    error.value = e.detail?.detail || e.message;
  } finally {
    loading.value = false;
  }
}

function confirmDelete(gp) {
  actionError.value = null;
  pendingDelete.value = gp;
}

async function doDelete() {
  const gp = pendingDelete.value;
  pendingDelete.value = null;
  deleting.value = gp.id;
  actionError.value = null;
  try {
    await apiFetch(`/api/admin/grammar-points/${gp.id}`, { method: "DELETE" });
    items.value = items.value.filter(x => x.id !== gp.id);
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
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.admin-page-header h2 { margin: 0; }

.admin-table-wrap { overflow-x: auto; }

.admin-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.admin-table th {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-muted);
  font-weight: 500;
}
.admin-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  vertical-align: middle;
}
.admin-table tr:last-child td { border-bottom: none; }

.level-chip {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  background: var(--bg-tertiary);
  color: var(--accent);
}
.item-title { font-weight: 500; }
.item-sub { font-size: 12px; margin-top: 2px; }
.mono { font-family: monospace; font-size: 13px; }

.row-actions { display: flex; gap: 6px; justify-content: flex-end; }

.btn.small { padding: 4px 10px; font-size: 12px; }
.btn.danger { background: var(--error); color: var(--text-on-accent); border-color: var(--error); }
.btn.danger:hover { opacity: 0.85; }

.error-msg { color: var(--error); padding: 12px 0; }

.confirm-overlay {
  position: fixed; inset: 0;
  background: var(--confirm-overlay);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
}
.confirm-dialog {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
}
.confirm-dialog h3 { margin: 0 0 8px; }
.confirm-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
</style>
