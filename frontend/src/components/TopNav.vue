<script setup>
import { useRouter, useRoute } from "vue-router";
import { useAuth } from "../composables/useAuth.js";

const router = useRouter();
const route = useRoute();
const { user, logout } = useAuth();

function handleLogout() {
  logout();
  router.push("/login");
}

const navItems = [
  { path: "/dashboard", label: "工作台", icon: "home" },
  { path: "/projects", label: "项目管理", icon: "folder" },
  { path: "/audit", label: "审核中心", icon: "chart" },
];

function isActive(itemPath) {
  if (itemPath === "/projects" && route.path.startsWith("/projects")) return true;
  if (itemPath === "/editor" && route.path.startsWith("/editor")) return true;
  return route.path === itemPath;
}
</script>

<template>
  <header class="bg-white border-b border-cosmic-border sticky top-0 z-50">
    <div class="max-w-[1280px] mx-auto px-6 h-14 flex items-center justify-between">
      <!-- Logo -->
      <div class="flex items-baseline gap-2 cursor-pointer" @click="router.push('/dashboard')">
        <span class="text-lg font-bold text-brand-primary">彩讯股份</span>
        <span class="text-xs text-slate-400 tracking-widest">RICHINFO</span>
      </div>

      <!-- Nav Links -->
      <nav class="hidden md:flex items-center gap-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
          :class="
            isActive(item.path)
              ? 'text-brand-primary bg-brand-primary/5'
              : 'text-cosmic-muted hover:text-cosmic-dark hover:bg-slate-50'
          "
        >
          {{ item.label }}
        </router-link>
      </nav>

      <!-- User -->
      <div class="flex items-center gap-4">
        <span class="text-sm text-cosmic-muted hidden sm:inline">
          {{ user?.display_name || user?.username }}
        </span>
        <button
          @click="handleLogout"
          class="text-sm text-cosmic-muted hover:text-cosmic-danger transition-colors"
        >
          退出
        </button>
      </div>
    </div>
  </header>
</template>
