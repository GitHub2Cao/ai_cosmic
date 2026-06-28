<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth.js";
import client from "../api/client.js";
import TopNav from "../components/TopNav.vue";

const route = useRoute();
const router = useRouter();
const { user } = useAuth();

const projectId = route.params.projectId;
const docType = route.params.docType; // requirement / cosmic / srs

const project = ref(null);
const document = ref(null);
const loading = ref(true);
const error = ref("");

async function loadData() {
  loading.value = true;
  try {
    const { data: p } = await client.get(`/projects/${projectId}`);
    project.value = p;
    // For Phase 3, we only show a skeleton; real content loading in Phase 4
    document.value = p.documents?.find((d) => d.type === docType);
  } catch (err) {
    error.value = err.response?.data?.detail || "加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);

const titleMap = {
  requirement: "需求文档",
  cosmic: "COSMIC 文档",
  srs: "SRS 需求规格说明书",
};
</script>

<template>
  <div class="min-h-screen bg-[#F0F4F8]">
    <TopNav />

    <!-- Editor layout -->
    <div class="pt-14">
      <!-- Toolbar / Breadcrumb -->
      <div class="bg-white border-b border-cosmic-border sticky top-14 z-40">
        <div class="max-w-[1440px] mx-auto px-4 h-12 flex items-center justify-between">
          <div class="flex items-center gap-3 text-sm">
            <button @click="router.push(`/projects/${projectId}`)" class="text-cosmic-muted hover:text-brand-primary transition-colors">
              {{ project?.name || "项目" }}
            </button>
            <span class="text-cosmic-border">/</span>
            <span class="text-cosmic-dark font-medium">{{ titleMap[docType] || "文档" }}</span>
            <span class="px-2 py-0.5 rounded text-xs bg-brand-primary/10 text-brand-primary">编辑模式</span>
          </div>
          <div class="flex items-center gap-2">
            <button class="px-4 py-1.5 rounded-btn text-sm text-cosmic-muted hover:bg-slate-50 border border-cosmic-border transition-colors">
              预览
            </button>
            <button class="px-4 py-1.5 rounded-btn gradient-btn text-sm">
              保存
            </button>
          </div>
        </div>
      </div>

      <!-- Three-column editor -->
      <div class="max-w-[1440px] mx-auto">
        <div class="grid grid-cols-1 lg:grid-cols-[260px_1fr_280px] min-h-[calc(100vh-112px)]">
          <!-- Left: Outline -->
          <aside class="hidden lg:block border-r border-cosmic-border bg-white p-4 overflow-y-auto">
            <h3 class="text-xs font-semibold text-cosmic-muted uppercase tracking-wider mb-3">文档大纲</h3>
            <nav class="space-y-1">
              <div v-for="i in 5" :key="i" class="px-3 py-2 rounded-lg text-sm text-cosmic-muted hover:bg-slate-50 cursor-pointer transition-colors">
                <span class="inline-block w-4 text-xs text-cosmic-muted/60">{{ i }}.</span>
                章节 {{ i }}
              </div>
            </nav>
          </aside>

          <!-- Center: Editor -->
          <main class="bg-white">
            <!-- Editor toolbar -->
            <div class="sticky top-[104px] z-30 bg-white/90 backdrop-blur border-b border-cosmic-border px-4 py-2 flex items-center gap-2 overflow-x-auto">
              <button class="px-2 py-1 rounded text-xs text-cosmic-muted hover:bg-slate-100 transition-colors font-bold">B</button>
              <button class="px-2 py-1 rounded text-xs text-cosmic-muted hover:bg-slate-100 transition-colors italic">I</button>
              <button class="px-2 py-1 rounded text-xs text-cosmic-muted hover:bg-slate-100 transition-colors underline">U</button>
              <div class="w-px h-4 bg-cosmic-border mx-1"></div>
              <button class="px-2 py-1 rounded text-xs text-cosmic-muted hover:bg-slate-100 transition-colors">H1</button>
              <button class="px-2 py-1 rounded text-xs text-cosmic-muted hover:bg-slate-100 transition-colors">H2</button>
              <button class="px-2 py-1 rounded text-xs text-cosmic-muted hover:bg-slate-100 transition-colors">H3</button>
            </div>

            <!-- Content area -->
            <div class="p-8 max-w-3xl mx-auto">
              <div v-if="loading" class="space-y-4">
                <div class="h-8 bg-slate-100 rounded w-2/3 animate-pulse"></div>
                <div class="h-4 bg-slate-100 rounded w-full animate-pulse"></div>
                <div class="h-4 bg-slate-100 rounded w-5/6 animate-pulse"></div>
                <div class="h-4 bg-slate-100 rounded w-4/5 animate-pulse"></div>
              </div>

              <div v-else-if="error" class="text-center py-12">
                <p class="text-cosmic-danger mb-2">{{ error }}</p>
                <button @click="loadData" class="text-brand-primary text-sm hover:underline">重试</button>
              </div>

              <div v-else class="space-y-6">
                <!-- Placeholder blocks for Phase 3 -->
                <div class="editable-block border-l-4 border-cosmic-success pl-4 py-2 rounded-r-lg bg-cosmic-success/[0.02]">
                  <p class="text-cosmic-dark text-sm leading-relaxed">
                    AI 生成的内容块示例。绿色左侧边框表示 AI 生成。
                    <span class="text-cosmic-muted">（编辑器将在 Phase 4 实现完整交互）</span>
                  </p>
                </div>
                <div class="editable-block border-l-4 border-cosmic-warning pl-4 py-2 rounded-r-lg bg-cosmic-warning/[0.02]">
                  <p class="text-cosmic-dark text-sm leading-relaxed">
                    人工编辑的内容块示例。橙色左侧边框表示人工修改。
                  </p>
                </div>
                <div class="p-6 rounded-lg border-2 border-dashed border-cosmic-border text-center">
                  <svg class="w-8 h-8 text-cosmic-muted mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <p class="text-sm text-cosmic-muted">点击添加内容块</p>
                </div>
              </div>
            </div>
          </main>

          <!-- Right: Stats -->
          <aside class="hidden lg:block border-l border-cosmic-border bg-white p-4 overflow-y-auto">
            <h3 class="text-xs font-semibold text-cosmic-muted uppercase tracking-wider mb-3">编辑统计</h3>
            <div class="space-y-4">
              <div class="p-3 rounded-lg border border-cosmic-border">
                <p class="text-xs text-cosmic-muted mb-2">AI 生成占比</p>
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div class="h-full bg-cosmic-success rounded-full" style="width: 78%"></div>
                  </div>
                  <span class="text-sm font-semibold text-cosmic-dark">78%</span>
                </div>
              </div>
              <div class="p-3 rounded-lg border border-cosmic-border">
                <p class="text-xs text-cosmic-muted mb-2">人工修改占比</p>
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div class="h-full bg-cosmic-warning rounded-full" style="width: 22%"></div>
                  </div>
                  <span class="text-sm font-semibold text-cosmic-dark">22%</span>
                </div>
              </div>
            </div>

            <h3 class="text-xs font-semibold text-cosmic-muted uppercase tracking-wider mb-3 mt-6">编辑历史</h3>
            <div class="space-y-3">
              <div v-for="i in 3" :key="i" class="flex gap-2 text-xs">
                <span class="w-1.5 h-1.5 rounded-full bg-brand-primary mt-1.5 shrink-0"></span>
                <div>
                  <p class="text-cosmic-dark">修改第 {{ i }} 节内容</p>
                  <p class="text-cosmic-muted">{{ 10 - i * 2 }} 分钟前</p>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.editable-block {
  transition: all 0.2s;
}
.editable-block:hover {
  background-color: rgba(0, 0, 0, 0.01);
}
</style>
