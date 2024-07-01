<script setup lang="ts">
// Import the necessary components
import { appState } from "@/lib/appState";
import { ImageViewer } from ".";
</script>

<template>
  <div v-if="!appState.secondViewer" class="size-full">
    <ImageViewer />
  </div>
  <div v-else-if="appState.secondViewer" class="flex size-full">
    <div class="h-full w-1/2">
      <ImageViewer />
    </div>
    <div class="ml-2 h-full w-1/2">
      <ImageViewer />
    </div>
  </div>
</template>
