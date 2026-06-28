<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import client from "../api/client.js";
import TopNav from "../components/TopNav.vue";

const router = useRouter();

const loading = ref(true);
const records = ref([]);
const filter = ref("all"); // all / pending / approved / rejected

const filters = [
  { key: "all", label: "全部" },
  { key: "pending", label: "待审核" },
  { key: "approved", label: "已通过" },
  { key: "rejected", label: "已驳回" },
];

const statusMap = {
  pending: { text: "待审核", dot: "bg-cosmic-warning", class: "bg-cosmic-warning/10 text-cosmic-warning" },
  approved: { text: "已通过", dot: "bg-cosmic-success", class: "bg-cosmic-success/10 text-cosmic-success" },
  rejected: { text: "已驳回", dot: "bg-cosmic-danger", class: "bg-cosmic-danger/10 text-cosmic-danger" },
};

async function loadRecords() {
  loading.value = true;
  try {
    // Phase 3: load projects and build mock audit records from documents in reviewing/approved/rejected status
    const { data: projects } = await client.get("/projects");
    const allRecords = [];
    for (const p of projects) {
      try {
        const { data: docs } = await client.get(`/projects/${p.id}/documents`);
        for (const d of docs) {
          if (["reviewing", "approved", "rejected"].includes(d.status)) {
            allRecords.push({
              id: d.id,
              project_name: p.name,
              doc_type: d.type,
              doc_type_label: d.type === "cosmic" ? "COSMIC" : "SRS",
              status: d.status,
              version: d.version,
              submitted_at: d.updated_at || d.created_at,
            });
          }
        }
      } catch (_) {
        // ignore per-project errors
      }
    }
    records.value = allRecords;
  } catch (err) {
    console.error("loadRecords error", err);
  } finally {
    loading.value = false;
  }
}

onMounted(loadRecords);

const filteredRecords = computed(() => {
  if (filter.value === "all") return records.value;
  return records.value.filter((r) => r.status === filter.value);
});
</script>

<template>
  <div class="min-h-screen bg-[#F0F4F8]">
    <TopNav />

    <main class="max-w-[1280px] mx-auto px-6 py-8">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-cosmic-dark">审核中心</h1>
          <p class="text-sm text-cosmic-muted mt-1">审核 COSMIC 文档与 SRS 需求规格说明书</p>
        </div>
      </div>

      <!-- Filter bar -->
      <div class="flex items-center gap-2 mb-6">
        <button
          v-for="f in filters"
          :key="f.key"
          @click="filter = f.key"
          class="px-4 py-2 rounded-full text-sm font-medium transition-colors"
          :class="
            filter === f.key
              ? 'bg-brand-primary text-white'
              : 'bg-white text-cosmic-muted border border-cosmic-border hover:bg-slate-50'
          "
        >
          {{ f.label }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="w-8 h-8 border-2 border-brand-primary/20 border-t-brand-primary rounded-full animate-spin"></div>
      </div>

      <!-- Empty -->
      <div v-else-if="filteredRecords.length === 0" class="bg-white rounded-card shadow-card border border-cosmic-border p-12 text-center">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
          <svg class="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        </div>
        <p class="text-cosmic-muted">暂无审核记录</p>
        <p class="text-sm text-cosmic-muted/70 mt-1">当项目文档进入审核状态时将显示在此</p>
      </div>

      <!-- Table -->
      <div v-else class="bg-white rounded-card shadow-card border border-cosmic-border overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-cosmic-border bg-slate-50/60">
              <th class="text-left font-medium text-cosmic-muted px-6 py-3">项目</th>
              <th class="text-left font-medium text-cosmic-muted px-6 py-3">文档类型</th>
              <th class="text-left font-medium text-cosmic-muted px-6 py-3">版本</th>
              <th class="text-left font-medium text-cosmic-muted px-6 py-3">状态</th>
              <th class="text-left font-medium text-cosmic-muted px-6 py-3">提交时间</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-cosmic-border/50">
            <tr
              v-for="record in filteredRecords"
              :key="record.id"
              class="hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <td class="px-6 py-4 font-medium text-cosmic-dark">{{ record.project_name }}</td>
              <td class="px-6 py-4">
                <span
                  class="px-2 py-0.5 rounded text-xs font-medium"
                  :class="record.doc_type === 'cosmic' ? 'bg-cosmic-success/10 text-cosmic-success' : 'bg-blue-50 text-blue-600'"
                >
                  {{ record.doc_type_label }}
                </span>
              </td>
              <td class="px-6 py-4 text-cosmic-muted">{{ record.version }}</td>
              <td class="px-6 py-4">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-medium flex items-center gap-1.5 inline-flex" :class="statusMap[record.status]?.class || 'bg-slate-100 text-slate-600'">
                  <span class="w-1.5 h-1.5 rounded-full" :class="statusMap[record.status]?.dot || 'bg-slate-400'"></span>
                  {{ statusMap[record.status]?.text || record.status }}
                </span>
              </td>
              <td class="px-6 py-4 text-cosmic-muted">
                {{ new Date(record.submitted_at).toLocaleDateString('zh-CN') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>
