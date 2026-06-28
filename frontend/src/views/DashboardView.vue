<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth.js";
import client from "../api/client.js";
import TopNav from "../components/TopNav.vue";

const router = useRouter();
const { user } = useAuth();
const projectCount = ref(0);
const activeCount = ref(0);
const loading = ref(true);

onMounted(async () => {
  try {
    const { data } = await client.get("/projects");
    projectCount.value = data.length;
    activeCount.value = data.filter((p) => p.status !== "approved").length;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="min-h-screen bg-[#F0F4F8]">
    <TopNav />

    <!-- 内容区 -->
    <main class="max-w-[1280px] mx-auto px-6 py-8">
      <h1 class="text-2xl font-bold text-cosmic-dark mb-6">工作台</h1>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white rounded-card shadow-card p-6 border border-cosmic-border">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-cosmic-muted mb-1">我的项目</p>
              <p class="text-3xl font-bold text-cosmic-dark">
                {{ loading ? "-" : projectCount }}
              </p>
            </div>
            <div class="w-12 h-12 rounded-xl bg-brand-primary/10 flex items-center justify-center text-brand-primary">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-card shadow-card p-6 border border-cosmic-border">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-cosmic-muted mb-1">进行中</p>
              <p class="text-3xl font-bold text-cosmic-dark">
                {{ loading ? "-" : activeCount }}
              </p>
            </div>
            <div class="w-12 h-12 rounded-xl bg-cosmic-success/10 flex items-center justify-center text-cosmic-success">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-card shadow-card p-6 border border-cosmic-border">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-cosmic-muted mb-1">快捷操作</p>
              <div class="flex gap-3 mt-2">
                <button
                  @click="router.push('/projects')"
                  class="px-4 py-2 rounded-btn gradient-btn text-sm"
                >
                  查看项目
                </button>
              </div>
            </div>
            <div class="w-12 h-12 rounded-xl bg-cosmic-warning/10 flex items-center justify-center text-cosmic-warning">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近项目 -->
      <div class="bg-white rounded-card shadow-card border border-cosmic-border overflow-hidden">
        <div class="px-6 py-4 border-b border-cosmic-border flex items-center justify-between">
          <h2 class="text-lg font-semibold text-cosmic-dark">欢迎使用 COSMIC</h2>
        </div>
        <div class="px-6 py-8 text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-brand-primary/10 flex items-center justify-center">
            <svg class="w-8 h-8 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p class="text-cosmic-muted mb-4">
            COSMIC 是彩讯股份基于大模型构建的智能文档转换平台，支持需求文档 → COSMIC → SRS 的全流程转换。
          </p>
          <button
            @click="router.push('/projects')"
            class="px-6 py-2.5 rounded-btn gradient-btn text-sm inline-flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            新建项目
          </button>
        </div>
      </div>
    </main>
  </div>
</template>
