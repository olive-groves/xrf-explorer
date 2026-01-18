<script setup lang="ts">
// Import the necessary components
import { Menubar } from "@/components/ui/menubar";
import { ExportMenu, FileMenu, MainMenu, WindowMenu, UserMenu, WorkSpaceMenu } from ".";
import { computed } from "vue";
import { appState } from "@/lib/appState";
import { saveWorkspaceDebounced } from "../image-viewer/workspace";

const workspace = computed(() => appState.workspace);

// Check wether we have partial spectral data
const hasPartialSpectral = computed(() => (workspace.value?.partialSpectralCubes?.length ?? 0) > 0);

// Check wether we have partial elemental data
const hasPartialElemental = computed(() => (workspace.value?.partialElementalCubes?.length ?? 0) > 0);

// Check wether we can redo stitching
const canRedoStitching = computed(() => {
  if (!workspace.value || appState.user.role === "VIEWER") return false;
  return workspace.value.stitchingMode === "full" && (hasPartialSpectral.value || hasPartialElemental.value);
});

/**
 * Function to restart stitching.
 */
function redoStitching() {
  if (!workspace.value) return;

  workspace.value.stitchingMode = "partial";

  saveWorkspaceDebounced();
}
</script>

<template>
  <Menubar class="m-0 h-min w-full justify-between rounded-none border-0 border-b">
    <div class="flex">
      <MainMenu />
      <FileMenu />
      <WindowMenu />
      <WorkSpaceMenu />
    </div>

    <div class="flex items-center gap-2">
      <!-- Show redo stiching button if applicable -->
      <Button v-if="canRedoStitching" variant="outline" size="sm" @click="redoStitching"> Redo stitching </Button>

      <UserMenu />
      <ExportMenu />
    </div>
  </Menubar>
</template>
