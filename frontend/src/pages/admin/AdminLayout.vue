<template>
  <div class="admin-shell">
    <nav class="admin-sidebar">
      <div class="admin-brand">
        <Icon name="lock" />
        Admin
      </div>

      <RouterLink class="admin-link" to="/admin/grammar" active-class="active">
        <Icon name="book" />
        Grammar
      </RouterLink>

      <RouterLink class="admin-link" to="/admin/vocab" active-class="active">
        <Icon name="tag" />
        Vocab
      </RouterLink>

      <RouterLink class="admin-link" to="/admin/prompts" active-class="active">
        <Icon name="clipboard" />
        Prompts
      </RouterLink>

      <div class="admin-sidebar-spacer"></div>

      <RouterLink class="admin-link back-link" to="/dashboard">
        <Icon name="arrow-left" />
        Back to dashboard
      </RouterLink>
    </nav>

    <main class="admin-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import Icon from "../../components/Icon.vue";
</script>

<style scoped>
.admin-shell {
  display: flex;
  min-height: calc(100vh - 60px);
}

.admin-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 16px 0;
  gap: 2px;
}

.admin-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px 16px;
  font-weight: 600;
  font-size: 14px;
  color: var(--accent);
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 8px;
}

.admin-brand svg {
  width: 16px;
  height: 16px;
}

.admin-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 14px;
  color: var(--text-muted);
  text-decoration: none;
  border-radius: 0;
  transition: background 0.15s, color 0.15s;
}

.admin-link:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.admin-link.active {
  background: var(--bg-tertiary);
  color: var(--accent);
  border-left: 2px solid var(--accent);
}

.admin-link svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.admin-sidebar-spacer {
  flex: 1;
}

.back-link {
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
  margin-top: 8px;
}

.admin-content {
  flex: 1;
  padding: 24px;
  overflow: auto;
}
</style>
