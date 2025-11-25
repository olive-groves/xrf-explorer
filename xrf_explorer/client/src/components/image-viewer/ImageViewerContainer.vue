<script setup lang="ts">
// Import the necessary components
import { pinnedGroups } from "@/lib/appState";
import { ImageViewer } from ".";
import { PinnedLayerCard } from "@/components/ui/slider";
</script>

<template>
  <div class="size-full">
    <ImageViewer />
    <div v-if="pinnedGroups.length" class="absolute left-1/2 top-2 z-50 flex -translate-x-1/2 flex-row space-x-2">
      <PinnedLayerCard v-for="group in pinnedGroups" :key="group.name" :group="group" @unpin="group.pinned = false" />
    </div>
  </div>
</template>
