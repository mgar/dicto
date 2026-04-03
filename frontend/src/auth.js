import { reactive } from "vue";
import { apiFetch } from "./api";

const state = reactive({
  user: null,
  loaded: false
});

export function useAuth() {
  async function loadMe() {
    try {
      const data = await apiFetch("/api/auth/me");
      state.user = data.user;
    } catch (e) {
      state.user = null;
    } finally {
      state.loaded = true;
    }
  }

  async function login(email, password) {
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    state.user = data.user;
    state.loaded = true;
  }

  async function loginWithGoogle(credential) {
    const data = await apiFetch("/api/auth/google", {
      method: "POST",
      body: JSON.stringify({ credential })
    });
    state.user = data.user;
    state.loaded = true;
  }

  async function logout() {
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
    } finally {
      state.user = null;
      state.loaded = true;
    }
  }

  return { state, loadMe, login, loginWithGoogle, logout };
}
