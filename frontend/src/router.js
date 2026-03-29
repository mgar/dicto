import { createRouter, createWebHistory } from "vue-router";
import Review from "./pages/Review.vue";
import Learn from "./pages/Learn.vue";
import Study from "./pages/Study.vue";
import Home from "./pages/Home.vue";
import Login from "./pages/Login.vue";
import Dashboard from "./pages/Dashboard.vue";
import GrammarList from "./pages/GrammarList.vue";
import GrammarDetail from "./pages/GrammarDetail.vue";
import VocabList from "./pages/VocabList.vue";
import VocabDetail from "./pages/VocabDetail.vue";
import AdminLayout from "./pages/admin/AdminLayout.vue";
import AdminGrammarList from "./pages/admin/AdminGrammarList.vue";
import AdminGrammarForm from "./pages/admin/AdminGrammarForm.vue";
import AdminVocabList from "./pages/admin/AdminVocabList.vue";
import AdminVocabForm from "./pages/admin/AdminVocabForm.vue";
import AdminPromptList from "./pages/admin/AdminPromptList.vue";
import AdminPromptForm from "./pages/admin/AdminPromptForm.vue";
import { useAuth } from "./auth";

const routes = [
  { path: "/", component: Home },
  
  { path: "/login", component: Login },
  { path: "/learn", component: Learn, meta: { requiresAuth: true } },
  { path: "/study", component: Study, meta: { requiresAuth: true } },
  { path: "/grammar", component: GrammarList, meta: { requiresAuth: true } },
  { path: "/grammar/:id", component: GrammarDetail, meta: { requiresAuth: true } },
  { path: "/vocab", component: VocabList, meta: { requiresAuth: true } },
  { path: "/vocab/:id", component: VocabDetail, meta: { requiresAuth: true } },
  { path: "/review", component: Review, meta: { requiresAuth: true } },
  { path: "/dashboard", component: Dashboard, meta: { requiresAuth: true } },
  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: "", redirect: "/admin/grammar" },
      { path: "grammar", component: AdminGrammarList },
      { path: "grammar/new", component: AdminGrammarForm },
      { path: "grammar/:id/edit", component: AdminGrammarForm },
      { path: "vocab", component: AdminVocabList },
      { path: "vocab/new", component: AdminVocabForm },
      { path: "vocab/:id/edit", component: AdminVocabForm },
      { path: "prompts", component: AdminPromptList },
      { path: "prompts/new", component: AdminPromptForm },
      { path: "prompts/:id/edit", component: AdminPromptForm },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to) => {
  const { state, loadMe } = useAuth();
  if (!state.loaded) await loadMe();

  if (to.meta.requiresAuth && !state.user) {
    return { path: "/login", query: { next: to.fullPath } };
  }
  if (to.meta.requiresAdmin && !state.user?.is_admin) {
    return { path: "/dashboard" };
  }
  if (to.path === "/login" && state.user) {
    return { path: "/dashboard" };
  }
});

export default router;
