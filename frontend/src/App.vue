<template>
  <div class="app-shell">
    <AppNavbar />
    <div class="app-main">
      <main class="container">
        <RouterView />
      </main>
    </div>
    <AppFooter v-if="showFooter" />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppNavbar from "./components/AppNavBar.vue";
import AppFooter from "./components/AppFooter.vue";

const route = useRoute();
const showFooter = computed(() => route.path !== "/review");
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import "open-props/normalize.min.css";
@import "open-props/open-props.min.css";

/* Theme CSS Variables */
:root,
[data-theme="dark"] {
  --bg-primary: #080d17;
  --bg-secondary: #0f1623;
  --bg-tertiary: #182030;
  --bg-card: #131d2e;
  --border-color: rgba(255, 255, 255, 0.07);
  --border-subtle: rgba(255, 255, 255, 0.04);
  --border-hover: #6366f1;
  --text-primary: #f0f4ff;
  --text-secondary: #c8d3e8;
  --text-muted: #7a8ba8;
  --accent: #6366f1;
  --accent-light: #818cf8;
  --accent-hover: #4f52e0;
  --accent-glow: rgba(99, 102, 241, 0.25);
  --violet: #a78bfa;
  --violet-glow: rgba(167, 139, 250, 0.2);
  --error: #f87171;
  --success: #34d399;
  --success-glow: rgba(52, 211, 153, 0.2);
  --gradient-start: #141d35;
  --gradient-end: #080d17;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4), 0 1px 4px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-glow: 0 0 24px rgba(99, 102, 241, 0.15);
  --accent-tint: rgba(99, 102, 241, 0.15);
  --violet-tint: rgba(167, 139, 250, 0.15);
  --error-tint: rgba(239, 68, 68, 0.08);
  --success-tint: rgba(52, 211, 153, 0.12);
  --radius-sm: var(--radius-1);
  --radius-md: var(--radius-2);
  --radius-lg: var(--radius-3);
  --space-1: var(--size-2);
  --space-2: var(--size-3);
  --space-3: var(--size-4);
  --space-4: var(--size-5);
  --space-5: var(--size-6);
  --space-6: var(--size-7);
  --text-sm: var(--font-size-1);
  --text-md: var(--font-size-2);
  --text-lg: var(--font-size-3);
  --transition-fast: all 140ms var(--ease-3);
  --transition-base: all 220ms var(--ease-3);
}

[data-theme="light"] {
  --bg-primary: #f4f6fb;
  --bg-secondary: #ffffff;
  --bg-tertiary: #eef1f8;
  --bg-card: #ffffff;
  --border-color: rgba(0, 0, 0, 0.07);
  --border-subtle: rgba(0, 0, 0, 0.04);
  --border-hover: #6366f1;
  --text-primary: #0d1117;
  --text-secondary: #2d3a4a;
  --text-muted: #64748b;
  --accent: #6366f1;
  --accent-light: #818cf8;
  --accent-hover: #4f52e0;
  --accent-glow: rgba(99, 102, 241, 0.12);
  --violet: #7c3aed;
  --violet-glow: rgba(124, 58, 237, 0.12);
  --error: #ef4444;
  --success: #10b981;
  --success-glow: rgba(16, 185, 129, 0.12);
  --gradient-start: #eef1fd;
  --gradient-end: #f4f6fb;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow-glow: 0 0 24px rgba(99, 102, 241, 0.08);
  --accent-tint: rgba(99, 102, 241, 0.1);
  --violet-tint: rgba(124, 58, 237, 0.1);
  --error-tint: rgba(239, 68, 68, 0.06);
  --success-tint: rgba(16, 185, 129, 0.08);
}

html {
  font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  font-feature-settings: "cv11", "ss01";
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background-color 0.25s ease, color 0.25s ease;
}

body {
  margin: 0;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
}

#app {
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-main {
  flex: 1;
}

/* Rich background gradient */
[data-theme="dark"] body {
  background: 
    radial-gradient(ellipse 100% 60% at 50% -10%, rgba(99, 102, 241, 0.1) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 80%, rgba(167, 139, 250, 0.05) 0%, transparent 50%),
    var(--bg-primary);
}

[data-theme="light"] body {
  background: 
    radial-gradient(ellipse 100% 60% at 50% -10%, rgba(99, 102, 241, 0.06) 0%, transparent 60%),
    var(--bg-primary);
}

a {
  color: inherit;
  text-decoration: none;
}

* {
  box-sizing: border-box;
}

.container {
  max-width: 1120px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-5);
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.card:hover {
  border-color: rgba(99, 102, 241, 0.25);
  box-shadow: var(--shadow-md);
}

[data-theme="light"] .card:hover {
  border-color: rgba(99, 102, 241, 0.15);
  box-shadow: var(--shadow-md);
}

.btn {
  background: var(--accent);
  border: 0;
  color: white;
  padding: 10px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-weight: 600;
  font-size: var(--text-sm);
  font-family: inherit;
  letter-spacing: -0.01em;
  transition: var(--transition-fast);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn:hover {
  background: var(--accent-hover);
  box-shadow: 0 4px 14px var(--accent-glow);
  transform: translateY(-1px);
}

.btn:active {
  transform: translateY(0);
  box-shadow: none;
}

.btn.secondary {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.btn.secondary:hover {
  background: var(--bg-tertiary);
  border-color: rgba(99, 102, 241, 0.4);
  color: var(--text-primary);
  box-shadow: none;
}

.btn.lg {
  padding: 12px 24px;
  font-size: 15px;
}

.btn.icon-only {
  width: 46px;
  height: 46px;
  padding: 0;
  justify-content: center;
}

.btn.icon-only svg,
.btn.lg svg {
  width: 18px;
  height: 18px;
}

[data-theme="light"] .btn.secondary {
  border-color: rgba(0, 0, 0, 0.12);
}

[data-theme="light"] .btn.secondary:hover {
  border-color: rgba(99, 102, 241, 0.3);
  background: var(--bg-tertiary);
}

.input {
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: var(--text-md);
  font-family: inherit;
  transition: var(--transition-fast);
  box-sizing: border-box;
}

.input:focus {
  outline: none;
  border-color: var(--accent);
  background: var(--bg-secondary);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.input::placeholder {
  color: var(--text-muted);
}

.row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* Utility classes */
.muted {
  color: var(--text-muted);
}

.surface {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.btn-row-center {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.ghost-btn {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-family: inherit;
  transition: var(--transition-fast);
}

.ghost-btn:hover {
  border-color: rgba(99, 102, 241, 0.35);
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}

.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}

.section-header-row h3 {
  margin: 0;
}

.stat-card {
  flex: 1;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 14px var(--space-4);
  text-align: center;
}

.segmented {
  display: flex;
}

.segmented .segment-btn {
  padding: 8px 14px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.segmented .segment-btn:first-child {
  border-radius: 8px 0 0 8px;
}

.segmented .segment-btn:last-child {
  border-radius: 0 8px 8px 0;
}

.segmented .segment-btn:not(:first-child) {
  border-left: none;
}

.segmented .segment-btn:hover {
  color: var(--text-primary);
}

.segmented .segment-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.stepper {
  display: flex;
  align-items: center;
}

.stepper .stepper-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 18px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.stepper .stepper-btn:first-child {
  border-radius: 8px 0 0 8px;
}

.stepper .stepper-btn:last-child {
  border-radius: 0 8px 8px 0;
}

.stepper .stepper-btn:hover {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.stepper .stepper-input {
  width: 60px;
  text-align: center;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-left: none;
  border-right: none;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

.inline-links {
  display: flex;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.inline-links a {
  color: var(--accent);
  font-size: 14px;
}

.inline-links a:hover {
  text-decoration: underline;
}

kbd {
  display: inline-block;
  padding: 2px 6px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 5px;
  font-family: inherit;
  font-size: 11px;
}

/* Spinner */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  width: 36px;
  height: 36px;
  border: 2.5px solid var(--border-color);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

/* Loading & Empty states */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.empty-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  background: var(--accent-glow);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon svg {
  width: 36px;
  height: 36px;
  color: var(--accent);
}

.empty-state h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.empty-state .muted {
  margin: 0 0 24px 0;
}

.empty-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* Back link */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 14px;
  margin-bottom: 16px;
  transition: color 0.2s;
}

.back-link:hover {
  color: var(--accent);
}

.back-icon {
  width: 18px;
  height: 18px;
}

/* Pill badge */
.pill {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  background: var(--accent);
  color: white;
  border-radius: 999px;
}

.pill.subtle {
  font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
}

/* Section icon */
.section-icon {
  width: 18px;
  height: 18px;
  color: var(--accent);
}

/* Button variants */
.btn.small {
  padding: 6px 12px;
  font-size: 13px;
}

.btn.danger {
  background: rgba(239, 68, 68, 0.9);
  color: white;
}

.btn.danger:hover {
  background: #dc2626;
  box-shadow: 0 4px 14px var(--error-tint);
}

/* Page header */
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
}

/* Mastery display */
.mastery-row {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.mastery-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: var(--accent-tint);
  color: var(--accent);
  border: 1px solid rgba(99, 102, 241, 0.35);
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
}

.mastery-meta {
  color: var(--text-muted);
  font-size: 13px;
}

/* Detail page layout */
.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.content-grid {
  display: grid;
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

/* Example blocks */
.example-spanish {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.example-spanish mark {
  background: var(--accent-tint);
  color: var(--accent);
  padding: 2px 4px;
  border-radius: 4px;
  font-weight: 600;
}

.example-english {
  color: var(--text-muted);
  font-size: 15px;
}

.example-notes {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
  font-size: 13px;
  color: var(--text-muted);
  font-style: italic;
}

/* Level list shared styles */
.levels-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.level-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.level-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.level-header:hover {
  background: var(--bg-primary);
}

.level-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chevron {
  width: 18px;
  height: 18px;
  color: var(--text-muted);
  transition: transform 0.2s;
}

.chevron.expanded {
  transform: rotate(90deg);
}

.level-name {
  font-weight: 600;
  font-size: 16px;
}

.level-count {
  color: var(--text-muted);
  font-size: 14px;
}

.level-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.level-content {
  border-top: 1px solid var(--border-color);
}

.list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px 12px 50px;
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s;
}

.list-item:last-child {
  border-bottom: none;
}

.list-item:hover {
  background: var(--bg-primary);
}

.list-item-link {
  flex: 1;
  text-decoration: none;
  color: inherit;
}

.list-item-info h4 {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.list-item-info .muted {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}

.list-item-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.prompts-count {
  font-size: 12px;
  color: var(--text-muted);
  padding: 4px 8px;
  background: var(--bg-primary);
  border-radius: 4px;
}

.prompts-count.complete {
  background: var(--violet-tint);
  color: var(--violet);
}

.checkbox-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 2px solid var(--border-color);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.checkbox-btn:hover {
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.05);
}

.checkbox-btn.selected {
  border-color: var(--accent);
  background: var(--accent);
  color: white;
}

.checkbox-btn svg {
  width: 16px;
  height: 16px;
}

.added-badge {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 2px solid var(--violet);
  color: var(--violet);
  background: rgba(167, 139, 250, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.added-badge svg {
  width: 16px;
  height: 16px;
}

.progress-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.progress-info .progress-text {
  font-size: 12px;
  color: var(--text-muted);
}

.progress-info .progress-bar {
  width: 100px;
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
}

.progress-info .progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s ease;
}

/* Chart shared styles */
.chart-card {
  padding: 22px 24px;
}

.chart-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.chart-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.chart-subtitle {
  margin: 3px 0 0 0;
  font-size: 12.5px;
  color: var(--text-muted);
}

.chart-controls {
  display: flex;
  gap: 4px;
}

.icon-btn {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.icon-btn:hover:not(:disabled) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-color: rgba(99, 102, 241, 0.4);
}

.icon-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.icon-btn svg {
  width: 14px;
  height: 14px;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.legend-dot {
  width: 12px;
  height: 8px;
  border-radius: 3px;
}

.legend-dot.vocab {
  background: var(--violet);
}

.legend-dot.grammar {
  background: var(--accent);
}

.chart-loading {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-size: 13px;
}

/* Mobile list adjustments */
@media (max-width: 640px) {
  .level-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .level-actions {
    width: 100%;
    justify-content: space-between;
  }

  .list-item {
    padding-left: 20px;
  }
}
</style>
