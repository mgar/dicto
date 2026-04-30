<template>
  <header class="nav">
    <div class="nav-inner">
      <RouterLink class="logo" :to="homeLink">
        <Icon name="book-closed" class="logo-icon" />
        <span class="logo-text">dicto</span>
      </RouterLink>

      <div class="spacer"></div>

      <div v-if="auth.state.user" class="links">
        <RouterLink class="link" to="/dashboard">
          <Icon name="grid" class="link-icon" />
          <span class="link-text">Dashboard</span>
        </RouterLink>

        <RouterLink class="link learn-link" :to="learnLink">
          <Icon name="book" class="link-icon" />
          <span class="link-text">Learn</span>
          <span v-if="counts.state.learnRemaining" class="pill nav-count learn-badge">
            {{ counts.state.learnRemaining }}
          </span>
        </RouterLink>

        <RouterLink class="link review-link" to="/review">
          <Icon name="check-circle" class="link-icon" />
          <span class="link-text">Review</span>
          <span v-if="counts.state.dueNow" class="pill nav-count review-badge">
            {{ counts.state.dueNow }}
          </span>
        </RouterLink>

        <div class="nav-divider"></div>

        <RouterLink class="link subtle" to="/grammar">Grammar</RouterLink>
        <RouterLink class="link subtle" to="/vocab">Vocab</RouterLink>
      </div>

      <!-- Theme toggle -->
      <button
        class="theme-toggle ghost-btn"
        @click="themeCtrl.toggle()"
        :title="themeCtrl.theme.value === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
      >
        <Icon v-if="themeCtrl.theme.value === 'dark'" name="sun" class="icon" />
        <Icon v-else name="moon" class="icon" />
      </button>

      <div v-if="auth.state.user" class="user-section" ref="userSection">
        <button class="user-btn" @click="toggleMenu">
          <div class="avatar">{{ auth.state.user.display_name.charAt(0).toUpperCase() }}</div>
        </button>

        <Transition name="menu">
          <div v-if="menuOpen" class="menu">
            <div class="menu-header">
              <span class="menu-name">{{ auth.state.user.display_name }}</span>
              <span class="menu-email">{{ auth.state.user.email }}</span>
            </div>
            <div class="menu-divider"></div>
            <RouterLink v-if="auth.state.user.is_admin" class="menu-item" to="/admin">
              <Icon name="lock" />
              Admin
            </RouterLink>
            <button class="menu-item" @click="doLogout">
              <Icon name="logout" />
              Logout
            </button>
          </div>
        </Transition>
      </div>

      <div v-else>
        <RouterLink class="btn login-btn" to="/login">
          Get Started
        </RouterLink>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from "vue";
import Icon from "./Icon.vue";
import { useRouter } from "vue-router";
import { useAuth } from "../auth";
import { useTheme } from "../theme";
import { useCounts } from "../counts";

const router = useRouter();
const auth = useAuth();
const themeCtrl = useTheme();
const counts = useCounts();
const menuOpen = ref(false);
const userSection = ref(null);

const homeLink = computed(() => (auth.state.user ? "/dashboard" : "/"));

// Go to Study if there are new items to learn, otherwise go to Learn page to add content
const learnLink = computed(() => {
  return counts.state.learnRemaining > 0 ? "/study" : "/learn";
});

function toggleMenu() {
  menuOpen.value = !menuOpen.value;
}

function handleOutsideClick(e) {
  if (menuOpen.value && userSection.value && !userSection.value.contains(e.target)) {
    menuOpen.value = false;
  }
}

async function doLogout() {
  await auth.logout();
  menuOpen.value = false;
  router.push("/");
}

onMounted(() => {
  if (auth.state.user) counts.refresh();
  document.addEventListener("mousedown", handleOutsideClick);
});

onUnmounted(() => {
  document.removeEventListener("mousedown", handleOutsideClick);
});

watch(
  () => auth.state.user,
  (u) => {
    if (u) counts.refresh();
  }
);
</script>

<style scoped>
/* Navigation bar */
.nav {
  position: sticky;
  top: 0;
  background: var(--nav-bg);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-bottom: 1px solid var(--nav-border);
  z-index: 100;
}

[data-theme="light"] .nav {
  background: var(--nav-bg);
  border-bottom: 1px solid var(--nav-border);
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Logo */
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px 6px 6px;
  border-radius: 10px;
  transition: background 0.18s ease;
}

.logo:hover {
  background: var(--nav-logo-hover-bg);
}

[data-theme="light"] .logo:hover {
  background: var(--nav-logo-hover-bg);
}

.logo-icon {
  width: 20px;
  height: 20px;
  color: var(--violet);
}

.logo-text {
  font-weight: 800;
  font-size: 19px;
  background: var(--accent-violet-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: var(--transparent);
  background-clip: text;
  letter-spacing: -0.6px;
}

.spacer { flex: 1; }

/* Navigation links */
.links {
  display: flex;
  align-items: center;
  gap: 2px;
}

.link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 11px;
  border-radius: 8px;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--text-muted);
  transition: all 0.18s ease;
  letter-spacing: -0.01em;
}

.link:hover {
  background: var(--nav-hover-bg);
  color: var(--text-primary);
}

[data-theme="light"] .link:hover {
  background: var(--nav-hover-bg);
}

.link.router-link-active {
  background: var(--nav-active-bg);
  color: var(--accent-light);
}

[data-theme="light"] .link.router-link-active {
  background: var(--nav-active-bg);
  color: var(--accent);
}

.link-icon {
  width: 16px;
  height: 16px;
  opacity: 0.65;
  flex-shrink: 0;
}

.link:hover .link-icon,
.link.router-link-active .link-icon {
  opacity: 1;
}

.link-text {
  display: none;
}

@media (min-width: 768px) {
  .link-text {
    display: inline;
  }
}

.link.subtle {
  color: var(--text-muted);
  font-weight: 400;
  font-size: 13px;
  padding: 7px 9px;
}

.link.subtle:hover {
  color: var(--text-secondary);
}

.nav-divider {
  width: 1px;
  height: 18px;
  background: var(--border-color);
  margin: 0 6px;
}

/* Badges */
.nav-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  font-size: 10.5px;
  line-height: 1;
}

.learn-badge {
  background: var(--violet-glow);
  color: var(--violet-light);
}

.review-badge {
  background: var(--accent-tint);
  color: var(--accent-light);
}

/* Theme toggle */
.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 9px;
}

[data-theme="light"] .theme-toggle {
  border-color: var(--border-color);
}

.theme-toggle:hover {
  background: var(--nav-hover-bg);
  color: var(--warning);
  border-color: var(--warning-fill);
}

[data-theme="light"] .theme-toggle:hover {
  background: var(--nav-hover-bg);
  color: var(--warning-hover);
  border-color: var(--warning-fill);
}

.icon {
  width: 16px;
  height: 16px;
}

/* User section */
.user-section {
  position: relative;
  margin-left: 4px;
}

.user-btn {
  display: flex;
  align-items: center;
  padding: 0;
  border: none;
  background: var(--transparent);
  cursor: pointer;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: var(--brand-gradient);
  color: var(--text-on-accent);
  font-weight: 700;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: box-shadow 0.18s ease, transform 0.18s ease;
  letter-spacing: -0.02em;
}

.user-btn:hover .avatar {
  transform: scale(1.06);
  box-shadow: 0 0 0 2px var(--nav-avatar-ring), 0 4px 12px var(--accent-border-subtle);
}

/* Dropdown menu */
.menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 224px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.menu-header {
  padding: 14px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--bg-tertiary);
}

.menu-name {
  font-weight: 600;
  font-size: 13.5px;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.menu-email {
  font-size: 12px;
  color: var(--text-muted);
}

.menu-divider {
  height: 1px;
  background: var(--border-color);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 11px 16px;
  background: var(--transparent);
  border: none;
  color: var(--text-secondary);
  font-size: 13.5px;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
  font-family: inherit;
}

.menu-item:hover {
  background: var(--error-tint);
  color: var(--error);
}

.menu-item svg {
  width: 16px;
  height: 16px;
  opacity: 0.7;
}

/* Menu animation */
.menu-enter-active,
.menu-leave-active {
  transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}

.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}

/* Login button */
.login-btn {
  background: var(--brand-gradient);
  padding: 9px 18px;
  border-radius: 9px;
  font-size: 13.5px;
}

.login-btn:hover {
  box-shadow: 0 4px 16px var(--accent-border);
}

/* Mobile adjustments */
@media (max-width: 640px) {
  .nav-inner {
    padding: 9px 12px;
    gap: 3px;
  }

  .nav-divider,
  .link.subtle {
    display: none;
  }

  .link {
    padding: 7px 8px;
  }

  .nav-count {
    min-width: 16px;
    height: 16px;
    font-size: 9.5px;
  }
}
</style>
