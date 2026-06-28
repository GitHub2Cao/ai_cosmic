<script setup>
import { computed } from "vue";

const props = defineProps({
  type: { type: String, required: true }, // requirement / cosmic / srs
  document: { type: Object, default: null },
  isAdmin: { type: Boolean, default: false },
});

const emit = defineEmits(["upload", "action"]);

const docTypeConfig = {
  requirement: {
    title: "需求文档",
    subtitle: "Word / Excel",
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
    accentColor: "text-blue-600",
    accentBg: "bg-blue-50",
    borderColor: "border-blue-200",
  },
  cosmic: {
    title: "COSMIC 文档",
    subtitle: "Excel 功能用户需求",
    icon: "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
    accentColor: "text-cosmic-success",
    accentBg: "bg-cosmic-success/10",
    borderColor: "border-cosmic-success/20",
  },
  srs: {
    title: "SRS 需求规格说明书",
    subtitle: "Word 规格文档",
    icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
    accentColor: "text-purple-600",
    accentBg: "bg-purple-50",
    borderColor: "border-purple-200",
  },
};

const config = computed(() => docTypeConfig[props.type]);

const statusMap = {
  pending: { text: "待处理", dot: "bg-slate-400", class: "text-slate-500" },
  generating: { text: "生成中", dot: "bg-cosmic-warning", class: "text-cosmic-warning" },
  editing: { text: "编辑中", dot: "bg-blue-500", class: "text-blue-600" },
  reviewing: { text: "审核中", dot: "bg-cosmic-warning", class: "text-cosmic-warning" },
  approved: { text: "已通过", dot: "bg-cosmic-success", class: "text-cosmic-success" },
  rejected: { text: "已驳回", dot: "bg-cosmic-danger", class: "text-cosmic-danger" },
};

const sourceMap = {
  ai: { text: "AI 生成", class: "bg-cosmic-success/10 text-cosmic-success" },
  manual_upload: { text: "人工上传", class: "bg-brand-primary/10 text-brand-primary" },
  manual_edit: { text: "人工编辑", class: "bg-cosmic-warning/10 text-cosmic-warning" },
};

const docStatus = computed(() => {
  if (!props.document) return statusMap.pending;
  return statusMap[props.document.status] || statusMap.pending;
});

const docSource = computed(() => {
  if (!props.document) return null;
  return sourceMap[props.document.source] || null;
});

function onFileChange(e) {
  const file = e.target.files?.[0];
  if (file) emit("upload", file);
}

function triggerFileInput() {
  document.getElementById(`file-${props.type}`)?.click();
}
</script>

<template>
  <div
    class="bg-white rounded-card shadow-card border border-cosmic-border overflow-hidden flex flex-col"
  >
    <!-- Header -->
    <div class="px-5 py-4 border-b border-cosmic-border/50 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="config.accentBg">
          <svg class="w-5 h-5" :class="config.accentColor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="config.icon" />
          </svg>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-cosmic-dark">{{ config.title }}</h3>
          <p class="text-xs text-cosmic-muted">{{ config.subtitle }}</p>
        </div>
      </div>
      <span
        class="px-2.5 py-0.5 rounded-full text-xs font-medium flex items-center gap-1.5"
        :class="docStatus.class"
      >
        <span class="w-1.5 h-1.5 rounded-full" :class="docStatus.dot"></span>
        {{ docStatus.text }}
      </span>
    </div>

    <!-- Body -->
    <div class="p-5 flex-1 flex flex-col">
      <!-- Existing document -->
      <template v-if="document">
        <div class="space-y-3 mb-4">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600">
              {{ document.version || "v1.0" }}
            </span>
            <span v-if="docSource" class="px-2 py-0.5 rounded text-xs font-medium" :class="docSource.class">
              {{ docSource.text }}
            </span>
          </div>
          <p class="text-sm text-cosmic-dark font-medium truncate">{{ document.original_filename || document.title || "未命名文档" }}</p>
          <div class="text-xs text-cosmic-muted">
            上传于 {{ new Date(document.created_at).toLocaleDateString("zh-CN") }}
          </div>
        </div>

        <!-- Actions -->
        <div class="grid grid-cols-2 gap-2 mt-auto">
          <button
            @click="triggerFileInput"
            class="px-3 py-2 rounded-btn text-xs font-medium border border-cosmic-border text-cosmic-muted hover:bg-slate-50 transition-colors flex items-center justify-center gap-1"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            替换
          </button>
          <a
            v-if="document.id"
            :href="`/api/documents/${document.id}/download`"
            class="px-3 py-2 rounded-btn text-xs font-medium border border-cosmic-border text-cosmic-muted hover:bg-slate-50 transition-colors flex items-center justify-center gap-1"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            下载
          </a>
        </div>
      </template>

      <!-- Empty / Upload state -->
      <template v-else>
        <div
          class="flex-1 flex flex-col items-center justify-center py-6 border-2 border-dashed border-cosmic-border rounded-lg mb-4 hover:border-brand-primary/40 hover:bg-brand-primary/[0.02] transition-colors cursor-pointer"
          @click="triggerFileInput"
        >
          <svg class="w-8 h-8 text-cosmic-muted mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p class="text-xs text-cosmic-muted text-center">
            <span v-if="type === 'requirement'">点击或拖拽上传<br>支持 .docx / .xlsx</span>
            <span v-else>暂无可操作文档<br>请先完成前置步骤</span>
          </p>
        </div>
      </template>

      <input type="file" :id="`file-${type}`" class="hidden" accept=".docx,.xlsx" @change="onFileChange" />
    </div>

    <!-- Footer -->
    <div class="px-5 py-3 border-t border-cosmic-border/50 bg-slate-50/50">
      <button
        v-if="type === 'requirement'"
        @click="emit('action', 'convert-cosmic')"
        class="w-full py-2 rounded-btn gradient-btn text-sm font-medium flex items-center justify-center gap-2"
        :disabled="!document"
        :class="{ 'opacity-50 cursor-not-allowed': !document }"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        AI 转 COSMIC
      </button>

      <button
        v-else-if="type === 'cosmic'"
        @click="emit('action', 'convert-srs')"
        class="w-full py-2 rounded-btn gradient-btn text-sm font-medium flex items-center justify-center gap-2"
        :disabled="!document"
        :class="{ 'opacity-50 cursor-not-allowed': !document }"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        AI 转 SRS
      </button>

      <button
        v-else-if="type === 'srs'"
        @click="emit('action', 'submit-audit')"
        class="w-full py-2 rounded-btn gradient-btn text-sm font-medium flex items-center justify-center gap-2"
        :disabled="!document"
        :class="{ 'opacity-50 cursor-not-allowed': !document }"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        提交审核
      </button>
    </div>
  </div>
</template>
