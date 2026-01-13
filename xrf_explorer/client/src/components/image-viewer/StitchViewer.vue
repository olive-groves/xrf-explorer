<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch } from "vue";
import StitchMappingViewer from "./StitchMappingViewer.vue";
import StitchPreviewViewer from "./StitchPreviewViewer.vue";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { canPreview } from "./stitchPoints";
import { fetchOptimalStitchInfo } from "./stitchHelper";
import { getTooltipByKey } from "@/lib/useToolTips";

// Local mode state
const mode = ref<"edit" | "preview">("edit");

/**
 * Handle requests for preview info from other components.
 */
function onRequestPreview() {
  if (mode.value === "preview" && lastPreviewInfo) {
    dispatchPreview(lastPreviewInfo);
  }
}

onMounted(() => {
  window.addEventListener("stitchViewer:requestPreviewInfo", onRequestPreview);
});

onUnmounted(() => {
  mode.value = "edit";
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

// cache last preview info so late listeners can still get it
let lastPreviewInfo: PreviewInfo | null = null;

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

const isLoading = ref(false);

// Whenever mode changes fetch stitchinfo, and show loading screen while generating greyscales
watch(mode, async (newMode) => {
  window.dispatchEvent(new CustomEvent("stitchViewer:modeChanged", { detail: newMode }));

  if (newMode !== "preview") return;

  isLoading.value = true; // show loading

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
    isLoading.value = false; // hide loading
  }
});

</script>

<template>
  <div class="flex h-full flex-col">
    <!-- Toggle Button -->
    <ToggleGroup type="single" v-model="mode" class="mb-2 space-x-2">
      <ToggleGroupItem value="edit" variant="outline" :title="getTooltipByKey('stitch.edit')">Edit</ToggleGroupItem>

      <div :title="!canPreview ? getTooltipByKey('stitch.no_preview') : getTooltipByKey('stitch.preview')">
        <ToggleGroupItem value="preview" variant="outline" :disabled="!canPreview"> Preview </ToggleGroupItem>
      </div>
    </ToggleGroup>

    <!-- Viewer -->
    <div class="flex-1 overflow-hidden relative">
      <StitchMappingViewer v-if="mode === 'edit'" class="size-full" />
      <StitchPreviewViewer v-else class="size-full" />

      <div
        v-if="isLoading"
        class="absolute inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      >
        <div class="rounded-lg bg-background px-6 py-4 shadow-lg flex items-center gap-3">
          <span class="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <span class="text-sm font-medium">generating greyscales</span>
        </div>
      </div>
    </div>
  </div>
</template>
