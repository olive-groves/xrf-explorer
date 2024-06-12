<script setup lang="ts">
import { secondViewer } from "@/lib/appState";
import { ImageViewer } from ".";
</script>

<template>
  <div v-if="!secondViewer" class="size-full">
    <ImageViewer />
  </div>
  <div v-else-if="secondViewer" class="flex size-full">
    <div class="h-full w-1/2">
      <ImageViewer />
    </div>
    <div class="ml-2 h-full w-1/2">
      <ImageViewer />
    </div>
  </div>
</template>
