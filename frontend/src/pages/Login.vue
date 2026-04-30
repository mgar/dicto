<template>
  <div class="login-wrapper">
    <div class="login-card card">
      <div class="login-header">
        <div class="login-icon">
          <Icon name="book" stroke-width="1.5" />
        </div>
        <h2>Welcome back</h2>
        <p class="muted">Use the credentials provided by the admin.</p>
      </div>

      <form @submit.prevent="onSubmit" class="login-form">
        <div class="field">
          <label>Email</label>
          <input class="input" v-model="email" type="email" autocomplete="username" required placeholder="you@example.com" />
        </div>

        <div class="field">
          <label>Password</label>
          <input class="input" v-model="password" type="password" autocomplete="current-password" required placeholder="••••••••" />
        </div>

        <button class="btn login-submit" :disabled="loading">
          {{ loading ? "Signing in..." : "Sign in" }}
        </button>

        <div v-if="showGoogle" class="divider"><span>or</span></div>

        <div v-if="showGoogle" class="google-login">
          <div ref="googleButtonRef"></div>
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>
      </form>
    </div>
  </div>
</template>
  
  <script setup>
  import { onMounted, ref } from "vue";
  import { useRouter, useRoute } from "vue-router";
  import { useAuth } from "../auth";
  import Icon from "../components/Icon.vue";
  
  const auth = useAuth();
  const router = useRouter();
  const route = useRoute();
  
  const email = ref("");
  const password = ref("");
  const loading = ref(false);
  const error = ref("");
  const googleButtonRef = ref(null);
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
  const showGoogle = !!googleClientId;

  function loadGoogleScript() {
    return new Promise((resolve, reject) => {
      if (window.google?.accounts?.id) {
        resolve();
        return;
      }

      const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (existing) {
        existing.addEventListener("load", () => resolve(), { once: true });
        existing.addEventListener("error", () => reject(new Error("Failed to load Google script")), { once: true });
        return;
      }

      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Failed to load Google script"));
      document.head.appendChild(script);
    });
  }

  async function onGoogleCredential(response) {
    const credential = response?.credential;
    if (!credential) {
      error.value = "Google sign-in failed.";
      return;
    }

    loading.value = true;
    error.value = "";
    try {
      await auth.loginWithGoogle(credential);
      const next = route.query.next || "/dashboard";
      router.push(next);
    } catch {
      error.value = "Google sign-in failed.";
    } finally {
      loading.value = false;
    }
  }

  async function setupGoogleButton() {
    if (!showGoogle || !googleButtonRef.value) return;

    await loadGoogleScript();
    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: onGoogleCredential,
      ux_mode: "popup"
    });
    window.google.accounts.id.renderButton(googleButtonRef.value, {
      theme: "outline",
      size: "large",
      width: 420,
      text: "signin_with",
      shape: "pill"
    });
  }
  
  async function onSubmit() {
    loading.value = true;
    error.value = "";
    try {
      await auth.login(email.value, password.value);
      const next = route.query.next || "/dashboard";
      router.push(next);
    } catch {
      error.value = "Invalid email or password.";
    } finally {
      loading.value = false;
    }
  }

  onMounted(async () => {
    try {
      await setupGoogleButton();
    } catch {
      // Keep email/password login working even if Google script fails.
    }
  });
  </script>
  
  <style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px 0 40px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 36px 32px;
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-icon {
  width: 52px;
  height: 52px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, var(--accent-tint), var(--violet-tint));
  border: 1px solid var(--accent-border-subtle);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-icon svg {
  width: 26px;
  height: 26px;
  color: var(--accent-light);
}

.login-header h2 {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.login-header .muted {
  margin: 0;
  font-size: 13.5px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.field label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.login-submit {
  width: 100%;
  justify-content: center;
  padding: 12px 20px;
  font-size: 15px;
  border-radius: 11px;
  background: var(--brand-gradient);
  margin-top: 6px;
  box-shadow: 0 4px 16px var(--accent-border);
}

.login-submit:hover:not(:disabled) {
  box-shadow: 0 6px 20px var(--accent-border);
  transform: translateY(-1px);
}

.login-submit:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 18px 0;
  color: var(--text-muted);
  font-size: 12px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-color);
}

.google-login {
  display: flex;
  justify-content: center;
  margin-bottom: 4px;
}

.error-msg {
  margin: 12px 0 0;
  color: var(--error);
  font-size: 13.5px;
  text-align: center;
}
</style>
