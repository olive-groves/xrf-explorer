<script setup lang="ts">
// Import the necessary components
import { appState, pinnedGroups } from "@/lib/appState";
import { ImageViewer } from ".";
import { PinnedLayerCard } from "@/components/ui/slider";
</script>

<template>
  <div v-if="!appState.secondViewer" class="size-full">
    <ImageViewer />
    <div
        v-if="pinnedGroups.length"
        class="absolute top-2 left-1/2 -translate-x-1/2 z-50 flex flex-row space-x-2"
      >
        <PinnedLayerCard
          v-for="group in pinnedGroups"
          :key="group.name"
          :group="group"
          @unpin="group.pinned = false"
        />
      </div>
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
