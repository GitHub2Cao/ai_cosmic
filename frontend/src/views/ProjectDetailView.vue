<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth.js";
import client from "../api/client.js";
import TopNav from "../components/TopNav.vue";
import DocCard from "../components/DocCard.vue";

const route = useRoute();
const router = useRouter();
const { user } = useAuth();
const projectId = route.params.id;

const project = ref(null);
const loading = ref(true);
const error = ref("");
const currentIteration = ref(null);

const showIterationSelector = ref(false);
const showNewIteration = ref(false);
const newIterationName = ref("");
const newIterationSummary = ref("");
const creatingIteration = ref(false);

const showAddMember = ref(false);
const newMember = ref({ username: "", role: "editor" });
const addingMember = ref(false);

const editingContext = ref(false);
const contextDraft = ref("");
const savingContext = ref(false);
const uploading = ref(false);

const isAdmin = computed(() => {
  if (!project.value || !user.value) return false;
  return project.value.members.some(
    (m) => m.id === user.value.id && m.role === "admin"
  );
});

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
const statusTip = {
  draft: "项目刚创建，尚未开始 AI 转换",
  converting: "正在进行需求文档 → COSMIC 或 SRS 的 AI 转换",
  reviewing: "生成的 COSMIC/SRS 文档正在审核中",
  approved: "项目文档已通过审核，流程完成",
};

const roleText = {
  admin: "管理员",
  editor: "编辑者",
  viewer: "查看者",
};

// Document helpers (from current iteration)
const requirementDoc = computed(() =>
  currentIteration.value?.documents?.requirement
);
const cosmicDoc = computed(() =>
  currentIteration.value?.documents?.cosmic
);
const srsDoc = computed(() =>
  currentIteration.value?.documents?.srs
);

// Pipeline state
const pipelineNodes = computed(() => {
  const s = project.value?.status || "draft";
  const nodes = [
    { name: "需求文档", key: "requirement", state: "pending" },
    { name: "COSMIC", key: "cosmic", state: "pending" },
    { name: "SRS", key: "srs", state: "pending" },
    { name: "审核完成", key: "audit", state: "pending" },
  ];

  if (s === "draft") {
    nodes[0].state = requirementDoc.value ? "done" : "active";
  } else if (s === "converting") {
    nodes[0].state = "done";
    nodes[1].state = "active";
  } else if (s === "reviewing") {
    nodes[0].state = "done";
    nodes[1].state = "done";
    nodes[2].state = "done";
    nodes[3].state = "active";
  } else if (s === "approved") {
    nodes.forEach((n) => (n.state = "done"));
  }
  return nodes;
});

async function loadProject() {
  loading.value = true;
  error.value = "";
  try {
    const { data } = await client.get(`/projects/${projectId}`);
    project.value = data;
    // Set current iteration from API
    if (data.current_iteration) {
      currentIteration.value = data.current_iteration;
    } else if (data.iterations && data.iterations.length > 0) {
      currentIteration.value = data.iterations.find(i => i.is_current) || data.iterations[0];
    }
  } catch (err) {
    error.value = err.response?.data?.detail || "加载项目失败";
  } finally {
    loading.value = false;
  }
}

onMounted(loadProject);

async function addMember() {
  if (!newMember.value.username.trim()) return;
  addingMember.value = true;
  try {
    await client.post(`/projects/${projectId}/members`, {
      username: newMember.value.username.trim(),
      role: newMember.value.role,
    });
    showAddMember.value = false;
    newMember.value = { username: "", role: "editor" };
    await loadProject();
  } catch (err) {
    alert(err.response?.data?.detail || "添加成员失败");
  } finally {
    addingMember.value = false;
  }
}

async function removeMember(userId) {
  if (!confirm("确定移除此成员吗？")) return;
  try {
    await client.delete(`/projects/${projectId}/members/${userId}`);
    await loadProject();
  } catch (err) {
    alert(err.response?.data?.detail || "移除成员失败");
  }
}

function startEditContext() {
  contextDraft.value = project.value.context_json || "";
  editingContext.value = true;
}

async function saveContext() {
  savingContext.value = true;
  try {
    await client.put(`/projects/${projectId}`, {
      context_json: contextDraft.value.trim() || null,
    });
    editingContext.value = false;
    await loadProject();
  } catch (err) {
    alert(err.response?.data?.detail || "保存失败");
  } finally {
    savingContext.value = false;
  }
}

// Upload document
async function uploadDocument(file, type) {
  uploading.value = true;
  const formData = new FormData();
  formData.append("type", type);
  formData.append("file", file);
  if (currentIteration.value?.id) {
    formData.append("iteration_id", currentIteration.value.id);
  }
  try {
    await client.post(`/projects/${projectId}/documents`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    await loadProject();
  } catch (err) {
    alert(err.response?.data?.detail || "上传失败");
  } finally {
    uploading.value = false;
  }
}

function handleDocAction(type, action) {
  if (action === "convert-cosmic") {
    alert("AI 转 COSMIC 功能将在 Phase 3.5 实现");
  } else if (action === "convert-srs") {
    alert("AI 转 SRS 功能将在 Phase 3.5 实现");
  } else if (action === "submit-audit") {
    alert("提交审核功能将在 Phase 4 实现");
  }
}

// Iteration management
async function switchIteration(iterationId) {
  showIterationSelector.value = false;
  if (!iterationId || iterationId === currentIteration.value?.id) return;
  loading.value = true;
  try {
    const { data } = await client.get(`/iterations/${iterationId}`);
    currentIteration.value = data;
  } catch (err) {
    alert(err.response?.data?.detail || "切换迭代失败");
  } finally {
    loading.value = false;
  }
}

function openNewIteration() {
  showIterationSelector.value = false;
  newIterationName.value = "";
  newIterationSummary.value = "";
  showNewIteration.value = true;
}

async function createIteration() {
  creatingIteration.value = true;
  try {
    const { data } = await client.post(`/projects/${projectId}/iterations`, {
      name: newIterationName.value.trim() || null,
      change_summary: newIterationSummary.value.trim() || null,
    });
    showNewIteration.value = false;
    // Refresh project and switch to new iteration
    await loadProject();
    if (data.id) {
      await switchIteration(data.id);
    }
  } catch (err) {
    alert(err.response?.data?.detail || "创建迭代失败");
  } finally {
    creatingIteration.value = false;
  }
}

// Mock diff stats for Phase 3
const diffStats = [
  {
    label: "COSMIC 文档",
    aiPercent: 78,
    humanPercent: 22,
    total: 12450,
    aiChars: 9711,
    humanAdd: 1800,
    humanDel: 1061,
  },
  {
    label: "SRS 文档",
    aiPercent: 65,
    humanPercent: 35,
    total: 8930,
    aiChars: 5804,
    humanAdd: 2100,
    humanDel: 1026,
  },
];

// Mock operation logs for Phase 3
const operationLogs = [
  {
    action: "创建项目",
    detail: "项目初始化完成",
    type: "user",
    time: "2024-06-20 10:30",
  },
  {
    action: "上传需求文档",
    detail: "需求文档 v1.0 上传完成",
    type: "user",
    time: "2024-06-20 11:00",
  },
  {
    action: "AI 转换",
    detail: "开始 COSMIC 文档生成",
    type: "system",
    time: "2024-06-20 11:05",
  },
];
</script>

<template>
  <div class="min-h-screen bg-[#F0F4F8]">
    <TopNav />

    <!-- 内容区 -->
    <main class="max-w-[1280px] mx-auto px-6 py-8">
      <!-- 返回 -->
      <button
        @click="router.push('/projects')"
        class="flex items-center gap-1 text-sm text-cosmic-muted hover:text-brand-primary transition-colors mb-4"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        返回项目列表
      </button>

      <!-- 加载中 -->
      <div v-if="loading" class="flex justify-center py-20">
        <div class="w-8 h-8 border-2 border-brand-primary/20 border-t-brand-primary rounded-full animate-spin"></div>
      </div>

      <!-- 错误 -->
      <div v-else-if="error" class="bg-white rounded-card shadow-card border border-cosmic-border p-12 text-center">
        <p class="text-cosmic-danger mb-2">{{ error }}</p>
        <button @click="loadProject" class="text-brand-primary hover:text-brand-accent text-sm">重试</button>
      </div>

      <template v-else-if="project">
        <!-- 项目信息卡片 -->
        <div class="bg-white rounded-card shadow-card border border-cosmic-border p-6 mb-6">
          <div class="flex items-center gap-3 mb-3">
            <h1 class="text-2xl font-bold text-cosmic-dark">{{ project.name }}</h1>
            <span
              class="px-2.5 py-0.5 rounded-full text-xs font-medium cursor-help"
              :class="statusClass[project.status] || 'bg-slate-100 text-slate-600'"
              :title="statusTip[project.status]"
            >
              {{ statusText[project.status] || project.status }}
            </span>
          </div>
          <p v-if="project.description" class="text-cosmic-muted mb-3">{{ project.description }}</p>
          <div class="flex items-center gap-4 text-xs text-cosmic-muted">
            <span>创建者：{{ project.creator?.display_name || project.creator?.username }}</span>
            <span>创建于 {{ new Date(project.created_at).toLocaleDateString('zh-CN') }}</span>
            <span>{{ project.members?.length || 0 }} 名成员</span>
          </div>
        </div>

        <!-- 迭代选择器 -->
        <div class="bg-white rounded-card shadow-card border border-cosmic-border p-4 mb-6">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span class="text-sm font-semibold text-cosmic-dark">当前迭代</span>
              <div class="relative">
                <button
                  @click="showIterationSelector = !showIterationSelector"
                  class="flex items-center gap-2 px-4 py-2 rounded-btn border border-cosmic-border text-sm hover:border-brand-primary transition-colors"
                >
                  <span class="font-medium">{{ currentIteration?.name || 'v1.0' }}</span>
                  <svg class="w-4 h-4 text-cosmic-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                <!-- Dropdown -->
                <div
                  v-if="showIterationSelector"
                  class="absolute top-full left-0 mt-1 w-56 bg-white rounded-card shadow-card border border-cosmic-border z-20 overflow-hidden"
                >
                  <div
                    v-for="iter in project.iterations"
                    :key="iter.id"
                    @click="switchIteration(iter.id)"
                    class="px-4 py-3 hover:bg-slate-50 cursor-pointer flex items-center justify-between"
                    :class="{ 'bg-brand-primary/[0.03]': currentIteration?.id === iter.id }"
                  >
                    <div>
                      <span class="text-sm font-medium text-cosmic-dark">{{ iter.name }}</span>
                      <span
                        class="ml-2 px-1.5 py-0.5 rounded text-[10px]"
                        :class="statusClass[iter.status] || 'bg-slate-100 text-slate-500'"
                      >
                        {{ statusText[iter.status] || iter.status }}
                      </span>
                    </div>
                    <span v-if="iter.is_current" class="text-xs text-brand-primary font-medium">当前</span>
                  </div>
                  <div class="border-t border-cosmic-border/50 px-4 py-3 hover:bg-slate-50 cursor-pointer" @click="openNewIteration">
                    <span class="text-sm text-brand-primary font-medium">+ 新建迭代</span>
                  </div>
                </div>
              </div>
              <p v-if="currentIteration?.change_summary" class="text-xs text-cosmic-muted hidden md:block">
                {{ currentIteration.change_summary }}
              </p>
            </div>
            <button
              v-if="isAdmin"
              @click="openNewIteration"
              class="px-4 py-2 rounded-btn border border-cosmic-border text-sm text-cosmic-dark hover:border-brand-primary hover:text-brand-primary transition-colors"
            >
              + 新建迭代
            </button>
          </div>
        </div>

        <!-- 转换流程可视化 -->
        <div class="bg-white rounded-card shadow-card border border-cosmic-border p-6 mb-6">
          <h2 class="text-sm font-semibold text-cosmic-muted uppercase tracking-wider mb-4">转换流程</h2>
          <div class="flex items-center justify-center gap-3 flex-wrap">
            <template v-for="(node, idx) in pipelineNodes" :key="node.key">
              <div
                class="flex flex-col items-center gap-1 px-4 py-3 rounded-lg border-2 min-w-[100px] transition-all"
                :class="{
                  'border-cosmic-success bg-cosmic-success/[0.03]': node.state === 'done',
                  'border-brand-primary bg-brand-primary/[0.03]': node.state === 'active',
                  'border-cosmic-border bg-slate-50/60': node.state === 'pending',
                }"
              >
                <div
                  class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                  :class="{
                    'bg-cosmic-success text-white': node.state === 'done',
                    'bg-brand-primary text-white': node.state === 'active',
                    'bg-slate-200 text-slate-500': node.state === 'pending',
                  }"
                >
                  <svg v-if="node.state === 'done'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                  </svg>
                  <span v-else>{{ idx + 1 }}</span>
                </div>
                <span class="text-xs font-medium" :class="node.state === 'pending' ? 'text-cosmic-muted' : 'text-cosmic-dark'">
                  {{ node.name }}
                </span>
              </div>
              <svg
                v-if="idx < pipelineNodes.length - 1"
                class="w-5 h-5 text-cosmic-border"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </template>
          </div>
        </div>

        <!-- 三文档卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <DocCard
            type="requirement"
            :document="requirementDoc"
            :is-admin="isAdmin"
            @upload="(file) => uploadDocument(file, 'requirement')"
            @action="(action) => handleDocAction('requirement', action)"
          />
          <DocCard
            type="cosmic"
            :document="cosmicDoc"
            :is-admin="isAdmin"
            @upload="(file) => uploadDocument(file, 'cosmic')"
            @action="(action) => handleDocAction('cosmic', action)"
          />
          <DocCard
            type="srs"
            :document="srsDoc"
            :is-admin="isAdmin"
            @upload="(file) => uploadDocument(file, 'srs')"
            @action="(action) => handleDocAction('srs', action)"
          />
        </div>

        <!-- 项目背景知识 -->
        <div class="bg-white rounded-card shadow-card border border-cosmic-border p-6 mb-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h2 class="text-lg font-semibold text-cosmic-dark">项目背景知识</h2>
            </div>
            <button v-if="isAdmin && !editingContext" @click="startEditContext" class="text-sm text-brand-primary hover:text-brand-accent font-medium">
              编辑
            </button>
          </div>

          <div v-if="editingContext" class="space-y-3">
            <p class="text-xs text-cosmic-muted">
              录入项目领域背景（JSON 或文本），用于 AI 转换时注入 Prompt 上下文，提升 COSMIC/SRS 生成准确率。
            </p>
            <textarea
              v-model="contextDraft"
              rows="6"
              class="w-full px-4 py-3 rounded-input border border-cosmic-border text-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10 font-mono resize-none"
              placeholder="例如：{ 'domain': '金融支付', 'language': '中文', 'functional_users': ['用户', '管理员'] }"
            ></textarea>
            <div class="flex items-center justify-end gap-3">
              <button @click="editingContext = false" class="px-4 py-2 rounded-btn text-sm text-cosmic-muted hover:bg-slate-50 border border-cosmic-border transition-colors">
                取消
              </button>
              <button
                @click="saveContext"
                :disabled="savingContext"
                class="px-4 py-2 rounded-btn gradient-btn text-sm disabled:opacity-60 flex items-center gap-2"
              >
                <span v-if="savingContext" class="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>
                {{ savingContext ? "保存中..." : "保存" }}
              </button>
            </div>
          </div>

          <div v-else-if="project.context_json" class="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <pre class="text-sm text-cosmic-dark whitespace-pre-wrap font-mono leading-relaxed">{{ project.context_json }}</pre>
          </div>
          <div v-else class="text-sm text-cosmic-muted py-4 text-center">
            暂无背景知识
            <span v-if="isAdmin" class="block mt-1">点击右上角「编辑」添加，帮助 AI 更好理解您的业务场景</span>
          </div>
        </div>

        <!-- 统计 + 日志 两列 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <!-- 人工修改量统计 -->
          <div class="bg-white rounded-card shadow-card border border-cosmic-border p-6">
            <h2 class="text-sm font-semibold text-cosmic-dark mb-4">人工修改量统计</h2>
            <div class="space-y-6">
              <div v-for="stat in diffStats" :key="stat.label" class="space-y-3">
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-cosmic-dark">{{ stat.label }}</span>
                  <span class="text-xs text-cosmic-muted">{{ stat.total.toLocaleString() }} 字符</span>
                </div>
                <!-- AI bar -->
                <div class="space-y-1">
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-cosmic-muted">AI 生成 {{ stat.aiPercent }}%</span>
                    <span class="text-cosmic-success font-medium">{{ stat.aiChars.toLocaleString() }}</span>
                  </div>
                  <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full"
                      :style="`width: ${stat.aiPercent}%; background: linear-gradient(90deg, #00D4AA, #00A884);`"
                    ></div>
                  </div>
                </div>
                <!-- Human bar -->
                <div class="space-y-1">
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-cosmic-muted">人工修改 {{ stat.humanPercent }}%</span>
                    <span class="text-cosmic-warning font-medium">+{{ stat.humanAdd }} / -{{ stat.humanDel }}</span>
                  </div>
                  <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full"
                      :style="`width: ${stat.humanPercent}%; background: linear-gradient(90deg, #F59E0B, #D97706);`"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 操作日志 -->
          <div class="bg-white rounded-card shadow-card border border-cosmic-border p-6">
            <h2 class="text-sm font-semibold text-cosmic-dark mb-4">操作日志</h2>
            <div class="space-y-4">
              <div v-for="(log, idx) in operationLogs" :key="idx" class="flex gap-3">
                <div class="mt-1">
                  <div
                    class="w-2 h-2 rounded-full"
                    :class="{
                      'bg-blue-500': log.type === 'user',
                      'bg-cosmic-success': log.type === 'system',
                      'bg-cosmic-warning': log.type === 'edit',
                    }"
                  ></div>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-cosmic-dark">{{ log.action }}</p>
                  <p class="text-xs text-cosmic-muted">{{ log.detail }}</p>
                  <p class="text-xs text-cosmic-muted/60 mt-0.5">{{ log.time }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 成员管理 -->
        <div class="bg-white rounded-card shadow-card border border-cosmic-border overflow-hidden">
          <div class="px-6 py-4 border-b border-cosmic-border flex items-center justify-between">
            <h2 class="text-lg font-semibold text-cosmic-dark">项目成员</h2>
            <button
              v-if="isAdmin"
              @click="showAddMember = true"
              class="px-4 py-2 rounded-btn gradient-btn text-sm inline-flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              添加成员
            </button>
          </div>

          <div v-if="!project.members || project.members.length === 0" class="px-6 py-12 text-center text-cosmic-muted">
            暂无成员（除创建者外）
          </div>

          <div v-else class="divide-y divide-cosmic-border/50">
            <div
              v-for="member in project.members"
              :key="member.project_member_id"
              class="px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
            >
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-brand-primary/10 flex items-center justify-center text-brand-primary text-sm font-medium">
                  {{ (member.display_name || member.username || 'U').charAt(0).toUpperCase() }}
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-cosmic-dark">
                      {{ member.display_name || member.username }}
                    </span>
                    <span
                      class="px-2 py-0.5 rounded-full text-[11px] font-medium"
                      :class="member.role === 'admin' ? 'bg-brand-primary/10 text-brand-primary' : 'bg-slate-100 text-slate-500'"
                    >
                      {{ roleText[member.role] || member.role }}
                    </span>
                  </div>
                  <div class="text-xs text-cosmic-muted mt-0.5">@{{ member.username }}</div>
                </div>
              </div>
              <div class="flex items-center gap-4">
                <span class="text-xs text-cosmic-muted">
                  {{ member.joined_at ? new Date(member.joined_at).toLocaleDateString('zh-CN') : '' }}
                </span>
                <button
                  v-if="isAdmin && (member.role !== 'admin' || project.members.filter(m => m.role === 'admin').length > 1)"
                  @click="removeMember(member.id)"
                  class="p-1.5 text-cosmic-muted hover:text-cosmic-danger transition-colors"
                  title="移除成员"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>

    <!-- 添加成员弹窗 -->
    <div v-if="showAddMember" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="showAddMember = false">
      <div class="bg-white rounded-card shadow-2xl w-full max-w-md mx-4 p-6">
        <h3 class="text-lg font-semibold text-cosmic-dark mb-4">添加成员</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-cosmic-dark mb-1.5">用户名 <span class="text-cosmic-danger">*</span></label>
            <input
              v-model="newMember.username"
              type="text"
              class="w-full px-4 py-3 rounded-input border border-cosmic-border text-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10"
              placeholder="请输入用户名"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-cosmic-dark mb-1.5">角色</label>
            <select
              v-model="newMember.role"
              class="w-full px-4 py-3 rounded-input border border-cosmic-border text-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10 bg-white"
            >
              <option value="editor">编辑者 — 可编辑文档</option>
              <option value="viewer">查看者 — 只读访问</option>
            </select>
          </div>
        </div>
        <div class="flex items-center justify-end gap-3 mt-6">
          <button @click="showAddMember = false" class="px-5 py-2.5 rounded-btn text-sm text-cosmic-muted hover:bg-slate-50 border border-cosmic-border transition-colors">
            取消
          </button>
          <button
            @click="addMember"
            :disabled="!newMember.username.trim() || addingMember"
            class="px-5 py-2.5 rounded-btn gradient-btn text-sm disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <span v-if="addingMember" class="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>
            {{ addingMember ? "添加中..." : "添加" }}
          </button>
        </div>
      </div>
    </div>
    <!-- 新建迭代弹窗 -->
    <div v-if="showNewIteration" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="showNewIteration = false">
      <div class="bg-white rounded-card shadow-2xl w-full max-w-md mx-4 p-6">
        <h3 class="text-lg font-semibold text-cosmic-dark mb-4">新建迭代</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-cosmic-dark mb-1.5">迭代名称</label>
            <input
              v-model="newIterationName"
              type="text"
              class="w-full px-4 py-3 rounded-input border border-cosmic-border text-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10"
              placeholder="如 v2.0，不填则自动生成"
            />
            <p class="text-xs text-cosmic-muted mt-1">不填将按 v1.0, v2.0, ... 自动生成</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-cosmic-dark mb-1.5">变更摘要（可选）</label>
            <textarea
              v-model="newIterationSummary"
              rows="3"
              class="w-full px-4 py-3 rounded-input border border-cosmic-border text-sm outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10 resize-none"
              placeholder="描述本轮迭代的需求变更..."
            ></textarea>
          </div>
        </div>
        <div class="flex items-center justify-end gap-3 mt-6">
          <button @click="showNewIteration = false" class="px-5 py-2.5 rounded-btn text-sm text-cosmic-muted hover:bg-slate-50 border border-cosmic-border transition-colors">
            取消
          </button>
          <button
            @click="createIteration"
            :disabled="creatingIteration"
            class="px-5 py-2.5 rounded-btn gradient-btn text-sm disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <span v-if="creatingIteration" class="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>
            {{ creatingIteration ? "创建中..." : "创建" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
