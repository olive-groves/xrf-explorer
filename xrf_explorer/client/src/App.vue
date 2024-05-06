<script setup lang="ts">
import Menu from "./components/Menu.vue";
import UploadSourceModal from "./components/UploadSourceModal.vue";
</script>

<template>
  <Menu />
  <UploadSourceModal class="hidden" />
</template>

<!-- Global styles -->
<style>
body {
  background-color: #443c3c;
}
</style>
