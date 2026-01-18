<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import StitchMappingViewer from "./StitchMappingViewer.vue";
import StitchPreviewViewer from "./StitchPreviewViewer.vue";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { canPreview } from "./stitchPoints";
import { fetchOptimalStitchInfo, stitchingInProgress } from "./stitchHelper";
import { getTooltipByKey } from "@/lib/useToolTips";
import { appState } from "@/lib/appState";

// Wether the backend is busy with computing the stitched datacube
const stitching = computed(() => stitchingInProgress.value);

const workspace = computed(() => appState.workspace);

// Wether we are editing or previewing
const mode = computed<"edit" | "preview">({
  get(): "edit" | "preview" {
    return appState.workspace?.mapping.mode ?? "edit";
  },
  set(v: "edit" | "preview") {
    if (!appState.workspace) return;
    appState.workspace.mapping.mode = v;
  },
});

// cache last preview info so late listeners can still get it
let lastPreviewInfo: PreviewInfo | null = null;

/**
 * Handle requests for preview info from preview window.
 */
function onRequestPreview() {
  const ws = appState.workspace;
  if (!ws) {
    return;
  }
  if (ws.mapping.mode === "preview" && lastPreviewInfo) {
    dispatchPreview(lastPreviewInfo);
  }
}

onMounted(() => {
  window.addEventListener("stitchViewer:requestPreviewInfo", onRequestPreview);
});

onUnmounted(() => {
  if (workspace.value) {
    workspace.value.mapping.mode = "edit";
  }
  window.removeEventListener("stitchViewer:requestPreviewInfo", onRequestPreview);
});

// Store preview info for stitchwindow to load
type PreviewInfo = {
  losses: number[];
  estimatedSize: number;
  optimalScaling?: number;
};

/**
 * Function to normalize raw preview info.
 * @param info - Raw preview info.
 * @param info.losses - Array of loss values or null.
 * @param info.estimatedSize - Estimated size of the stitch.
 * @param info.optimalScaling - Optional optimal scaling factor.
 * @returns Normalized preview info.
 */
function normalizePreviewInfo(info: {
  losses: number[] | null;
  estimatedSize: number;
  optimalScaling?: number;
}): PreviewInfo {
  return {
    losses: info.losses ?? [],
    estimatedSize: info.estimatedSize,
    optimalScaling: info.optimalScaling,
  };
}

/**
 * Function to send cached preview info.
 * @param info - The preview info to dispatch.
 */
function dispatchPreview(info: PreviewInfo) {
  window.dispatchEvent(
    new CustomEvent("stitchViewer:stichInfo", {
      detail: {
        mode: "preview",
        previewInfo: info,
      },
    }),
  );
}

// Wether we are still generating greyscales
const isLoading = ref(false);

// Whenever mode changes fetch stitchinfo, and show loading screen while generating greyscales
watch(
  () => workspace.value?.mapping.mode,
  async (newMode) => {
    if (!newMode) return;

    window.dispatchEvent(new CustomEvent("stitchViewer:modeChanged", { detail: newMode }));

    if (newMode !== "preview") return;

    isLoading.value = true;

    try {
      if (!lastPreviewInfo) {
        const raw = await fetchOptimalStitchInfo();
        if (!raw) return;
        lastPreviewInfo = normalizePreviewInfo(raw);
      }

      dispatchPreview(lastPreviewInfo);
    } catch (e) {
      console.warn("Failed to fetch stitch preview info", e);
    } finally {
      isLoading.value = false;
    }
  },
);
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- Toggle Button -->
    <ToggleGroup v-if="!stitching" type="single" v-model="mode" class="mb-2 space-x-2">
      <ToggleGroupItem value="edit" variant="outline" :title="getTooltipByKey('stitch.edit')">Edit</ToggleGroupItem>

      <div :title="!canPreview ? getTooltipByKey('stitch.no_preview') : getTooltipByKey('stitch.preview')">
        <ToggleGroupItem value="preview" variant="outline" :disabled="!canPreview"> Preview </ToggleGroupItem>
      </div>
    </ToggleGroup>

    <div class="relative flex-1 overflow-hidden">
      <StitchMappingViewer v-if="mode === 'edit' && !stitching" class="size-full" />
      <StitchPreviewViewer v-if="mode === 'preview' && !stitching" class="size-full" />

      <!-- Preview loading -->
      <div v-if="isLoading && !stitching" class="absolute inset-0 z-40">
        <span>Generating greyscales...</span>
      </div>

      <!-- Loading screen when stitching-->
      <div v-if="stitching" class="absolute inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
        <span class="size-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <span class="text-sm font-medium">Stitching in progress… (Do not close or change project)</span>
      </div>
    </div>
  </div>
</template>
