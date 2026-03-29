import { ref, watchEffect } from "vue";

const STORAGE_KEY = "dicto-theme";

// Check if user prefers dark mode
function getSystemPreference() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

// Get initial theme from storage or system preference
function getInitialTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return getSystemPreference();
}

const theme = ref(getInitialTheme());

// Apply theme to document
function applyTheme(newTheme) {
  document.documentElement.setAttribute("data-theme", newTheme);
}

// Initialize on load
applyTheme(theme.value);

// Watch for changes
watchEffect(() => {
  applyTheme(theme.value);
  localStorage.setItem(STORAGE_KEY, theme.value);
});

export function useTheme() {
  function toggle() {
    theme.value = theme.value === "dark" ? "light" : "dark";
  }

  function setTheme(newTheme) {
    theme.value = newTheme;
  }

  return {
    theme,
    toggle,
    setTheme,
    isDark: () => theme.value === "dark",
  };
}
