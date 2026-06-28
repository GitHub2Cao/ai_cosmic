import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import LoginView from "./views/LoginView.vue";
import RegisterView from "./views/RegisterView.vue";
import DashboardView from "./views/DashboardView.vue";
import ProjectsView from "./views/ProjectsView.vue";
import ProjectDetailView from "./views/ProjectDetailView.vue";
import DocumentEditorView from "./views/DocumentEditorView.vue";
import AuditView from "./views/AuditView.vue";
import { useAuth } from "./composables/useAuth.js";
import "./style.css";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: LoginView, meta: { guest: true } },
  { path: "/register", component: RegisterView, meta: { guest: true } },
  { path: "/dashboard", component: DashboardView, meta: { requiresAuth: true } },
  { path: "/projects", component: ProjectsView, meta: { requiresAuth: true } },
  { path: "/projects/:id", component: ProjectDetailView, meta: { requiresAuth: true } },
  { path: "/editor/:projectId/:docType", component: DocumentEditorView, meta: { requiresAuth: true } },
  { path: "/audit", component: AuditView, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const { isLoggedIn } = useAuth();
  const loggedIn = isLoggedIn();

  if (to.meta.requiresAuth && !loggedIn) {
    next("/login");
  } else if (to.meta.guest && loggedIn) {
    next("/dashboard");
  } else {
    next();
  }
});

const app = createApp(App);
app.use(router);
app.mount("#app");
