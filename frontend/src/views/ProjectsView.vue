<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth.js";
import client from "../api/client.js";
import TopNav from "../components/TopNav.vue";

const router = useRouter();
const { user } = useAuth();

const projects = ref([]);
const loading = ref(true);
const showModal = ref(false);
const newProject = ref({ name: "", description: "" });
const creating = ref(false);
const deleteConfirm = ref(null);

async function loadProjects() {
  loading.value = true;
  try {
    const { data } = await client.get("/projects");
    projects.value = data;
  } finally {
    loading.value = false;
  }
}

onMounted(loadProjects);

async function createProject() {
  if (!newProject.value.name.trim()) return;
  creating.value = true;
  try {
    await client.post("/projects", {
      name: newProject.value.name.trim(),
      description: newProject.value.description.trim() || undefined,
    });
    showModal.value = false;
    newProject.value = { name: "", description: "" };
    await loadProjects();
  } catch (err) {
    alert(err.response?.data?.detail || "创建失败");
  } finally {
    creating.value = false;
  }
}

async function deleteProject(id) {
  if (!confirm("确定要删除该项目吗？")) return;
  try {
    await client.delete(`/projects/${id}`);
    await loadProjects();
  } catch (err) {
    alert(err.response?.data?.detail || "删除失败");
  }
}

const statusText = {
  draft: "草稿",
  converting: "转换中",
  reviewing: "审核中",
  approved: "已通过",
};
const statusClass = {
  draft: "bg-slate-100 text-slate-600",
  converting: "bg-cosmic-warning/10 text-cosmic-warning",
  reviewing: "bg-blue-50 text-blue-600",
  approved: "bg-cosmic-success/10 text-cosmic-success",
};
</script>

<template>
  <div class="min-h-screen bg-[#F0F4F8]">
    <TopNav />

    <!-- 内容区 -->
    <header class="bg-white border-b border-cosmic-border sticky top-0 z-50">
      <div class="max-w-[1280px] mx-auto px-6 h-14 flex items-center justify-between">
        <div class="flex items-baseline gap-2 cursor-pointer" @click="router.push('/dashboard')">
          <span class="text-lg font-bold text-brand-primary">彩讯股份</span>
          <span class="text-xs text-slate-400 tracking-widest">RICHINFO</span>
        </div>
        <div class="flex items-center gap-4">
          <span class="text-sm text-cosmic-muted">{{ user?.display_name || user?.username }}</span>
          <button @click="handleLogout" class="text-sm text-cosmic-muted hover:text-cosmic-danger transition-colors">
            退出
          </button>
        </div>
      </div>
    </header>

    <!-- 内容区 -->
    <main class="max-w-[1280px] mx-auto px-6 py-8">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold text-cosmic-dark">项目管理</h1>
        <button
          @click="showModal = true"
          class="px-5 py-2.5 rounded-btn gradient-btn text-sm inline-flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          新建项目
        </button>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="w-8 h-8 border-2 border-brand-primary/20 border-t-brand-primary rounded-full animate-spin"></div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="projects.length === 0" class="bg-white rounded-card shadow-card border border-cosmic-border p-12 text-center">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
          <svg class="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        </div>
        <p class="text-cosmic-muted mb-2">暂无项目</p>
        <p class="text-sm text-cosmic-muted/70 mb-4">创建一个新项目开始 COSMIC 文档转换之旅</p>
        <button @click="showModal = true" class="px-5 py-2 rounded-btn gradient-btn text-sm">
          新建项目
        </button>
      </div>

      <!-- 项目列表 -->
      <div v-else class="grid grid-cols-1 gap-4">
        <div
          v-for="project in projects"
          :key="project.id"
          class="bg-white rounded-card shadow-card border border-cosmic-border p-6 hover:shadow-lg transition-shadow cursor-pointer group"
          @click="router.push(`/projects/${project.id}`)"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <h3 class="text-lg font-semibold text-cosmic-dark group-hover:text-brand-primary transition-colors">
                  {{ project.name }}
                </h3>
                <span class="px-2.5 py-0.5 rounded-full text-xs font-medium" :class="statusClass[project.status] || 'bg-slate-100 text-slate-600'">
                  {{ statusText[project.status] || project.status }}
                </span>
              </div>
              <p v-if="project.description" class="text-sm text-cosmic-muted mb-3">{{ project.description }}</p>
              <div class="flex items-center gap-4 text-xs text-cosmic-muted">
                <span class="flex items-center gap-1">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {{ project.creator?.display_name || project.creator?.username }}
                </span>
                <span class="flex items-center gap-1">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                  {{ project.member_count }} 名成员
                </span>
                <span class="flex items-center gap-1">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {{ new Date(project.created_at).toLocaleDateString('zh-CN') }}
                </span>
              </div>
            </div>
            <button
              @click.stop="deleteProject(project.id)"
              class="opacity-0 group-hover:opacity-100 p-2 text-cosmic-muted hover:text-cosmic-danger transition-all"
              title="删除项目"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- 新建项目弹窗 -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="showModal = false">
      <div class="bg-white rounded-card shadow-2xl w-full max-w-lg mx-4 p-6">
        <h3 class="text-lg font-semibold text-cosmic-dark mb-4">新建项目</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-cosmic-dark mb-1.5">项目名称 <span class="text-cosmic-danger">*</span></label>
            <input
              v-model="newProject.name"
              type="text"
              class="w-full px-4 py-3 rounded-input border border-cosmic-border text-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10"
              placeholder="请输入项目名称"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-cosmic-dark mb-1.5">项目描述</label>
            <textarea
              v-model="newProject.description"
              rows="3"
              class="w-full px-4 py-3 rounded-input border border-cosmic-border text-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10 resize-none"
              placeholder="简要描述项目内容（可选）"
            ></textarea>
          </div>
        </div>
        <div class="flex items-center justify-end gap-3 mt-6">
          <button @click="showModal = false" class="px-5 py-2.5 rounded-btn text-sm text-cosmic-muted hover:bg-slate-50 border border-cosmic-border transition-colors">
            取消
          </button>
          <button
            @click="createProject"
            :disabled="!newProject.name.trim() || creating"
            class="px-5 py-2.5 rounded-btn gradient-btn text-sm disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <span v-if="creating" class="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>
            {{ creating ? "创建中..." : "创建" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
