<script setup lang="ts">
import Menu from "./components/Menu.vue";
import UploadSourceModal from "./components/UploadSourceModal.vue";

import { ref } from "vue";

const isModalOpened = ref(false);
</script>

<template>
  <Menu @open-upload-modal="isModalOpened = true" />
  <UploadSourceModal
    @close-upload-modal="isModalOpened = false"
    v-if="isModalOpened"
  />
</template>

<!-- Global styles -->
<style>
body {
  background-color: #443c3c;
}
</style>
