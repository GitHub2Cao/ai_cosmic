<script setup>
import { onMounted } from "vue";
import { useAuth } from "./composables/useAuth.js";

const { init } = useAuth();

onMounted(() => {
  init();
});
</script>

<template>
  <router-view />
</template>
