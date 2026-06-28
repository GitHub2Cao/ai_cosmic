<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth.js";

const router = useRouter();
const { login } = useAuth();

const status = ref("checking");
const username = ref("");
const password = ref("");
const errorMsg = ref("");
const loading = ref(false);

onMounted(async () => {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    status.value = data.status === "ok" ? "ok" : "error";
  } catch {
    status.value = "error";
  }
});

async function handleLogin() {
  errorMsg.value = "";
  if (!username.value.trim() || !password.value) {
    errorMsg.value = "请输入用户名和密码";
    return;
  }
  loading.value = true;
  try {
    await login(username.value.trim(), password.value);
    router.push("/dashboard");
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || "登录失败，请重试";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-b from-[#F0F4F8] to-white">
    <div class="flex max-w-[1280px] w-full mx-auto px-10 min-h-screen">

      <!-- 左侧品牌区域 -->
      <div class="flex-1 flex flex-col justify-center pr-15">
        <div class="flex items-baseline gap-2.5 mb-12">
          <span class="text-xl font-bold text-brand-primary">cgm股份</span>
          <span class="text-[13px] text-slate-400 tracking-widest">CGM</span>
        </div>

        <h1 class="text-4xl font-bold text-cosmic-dark mb-6 leading-tight">
          AI 驱动的<br>文档智能转换平台
        </h1>
        <p class="text-[15px] text-cosmic-muted leading-relaxed mb-8 max-w-md">
          基于大模型技术，实现需求文档 → COSMIC → SRS 的全流程自动化转换与人工协作
        </p>

        <ul class="space-y-3 text-[15px] text-cosmic-muted">
          <li class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-brand-primary inline-block"></span>
            需求文档智能转换为 COSMIC 功能规模度量
          </li>
          <li class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-brand-primary inline-block"></span>
            COSMIC 自动生成需求规格说明书（SRS）
          </li>
          <li class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-brand-primary inline-block"></span>
            全流程人工修改追踪与管理员审核
          </li>
        </ul>
      </div>

      <!-- 右侧登录卡片区 -->
      <div class="flex-1 flex items-center justify-center">
        <div class="w-full max-w-[420px] bg-white rounded-card border border-cosmic-border shadow-card p-8">
          <h2 class="text-2xl font-bold text-cosmic-dark text-center mb-1">欢迎回来</h2>
          <p class="text-sm text-cosmic-muted text-center mb-8">登录到 COSMIC 工作台</p>

          <form @submit.prevent="handleLogin" class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-cosmic-dark mb-1.5">用户名 / 工号</label>
              <input
                v-model="username"
                type="text"
                class="w-full px-4 py-3 rounded-input border border-cosmic-border text-sm outline-none transition-all duration-200 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10"
                placeholder="请输入用户名"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-cosmic-dark mb-1.5">密码</label>
              <input
                v-model="password"
                type="password"
                class="w-full px-4 py-3 rounded-input border border-cosmic-border text-sm outline-none transition-all duration-200 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/10"
                placeholder="请输入密码"
              />
            </div>

            <!-- 错误信息 -->
            <div v-if="errorMsg" class="text-sm text-cosmic-danger bg-red-50 px-3 py-2 rounded-lg">
              {{ errorMsg }}
            </div>

            <div class="flex items-center justify-between text-sm">
              <label class="flex items-center gap-2 text-cosmic-muted cursor-pointer">
                <input type="checkbox" class="rounded border-cosmic-border" checked />
                记住我
              </label>
              <a href="#" class="text-brand-primary hover:text-brand-accent">忘记密码？</a>
            </div>
            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 rounded-btn gradient-btn text-[15px] disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span v-if="loading" class="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>
              {{ loading ? "登录中..." : "登录" }}
            </button>
          </form>

          <div class="mt-6 text-center text-sm text-cosmic-muted">
            还没有账号？
            <router-link to="/register" class="text-brand-primary hover:text-brand-accent font-medium">立即注册</router-link>
          </div>

          <div class="mt-6 flex items-center justify-center gap-2 text-xs text-cosmic-muted">
            <span
              class="inline-block w-2 h-2 rounded-full"
              :class="status === 'ok' ? 'bg-cosmic-success' : status === 'error' ? 'bg-cosmic-danger' : 'bg-cosmic-warning animate-pulse'"
            ></span>
            <span>
              后端服务 {{ status === 'ok' ? '已连接' : status === 'error' ? '未连接' : '连接中...' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
