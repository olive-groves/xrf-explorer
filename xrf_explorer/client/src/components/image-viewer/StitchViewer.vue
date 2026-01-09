<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch } from 'vue';
import StitchMappingViewer from './StitchMappingViewer.vue';
import StitchPreviewViewer from './StitchPreviewViewer.vue';
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { canPreview } from './stitchPoints';
import { fetchOptimalStitchInfo } from './stitchHelper';

// Local mode state
const mode = ref<'edit' | 'preview'>('edit');

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

// Send cached info
function dispatchPreview(info: PreviewInfo) {
  window.dispatchEvent(
    new CustomEvent("stitchViewer:stichInfo", {
      detail: {
        mode: "preview",
        previewInfo: info,
      },
    })
  );
}

// Whenever mode changes fetch stitchinfo
watch(mode, async (newMode) => {
  window.dispatchEvent(new CustomEvent("stitchViewer:modeChanged", { detail: newMode }));
  if (newMode !== "preview") return;
  try {
    if (!lastPreviewInfo) {
      const raw = await fetchOptimalStitchInfo();
      if (!raw) return;
      lastPreviewInfo = normalizePreviewInfo(raw);
    }
    dispatchPreview(lastPreviewInfo);
  } catch (e) {
    console.warn("Failed to fetch stitch preview info", e);
  }
});

</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Toggle Button -->
    <ToggleGroup type="single" v-model="mode" class="space-x-2 mb-2">
      <ToggleGroupItem value="edit" variant="outline">Edit</ToggleGroupItem>

      <div :title="!canPreview ? 'Can only preview after mapping 4 points for each greyscale' : ''">
        <ToggleGroupItem value="preview" variant="outline" :disabled="!canPreview">
          Preview
        </ToggleGroupItem>
      </div>
    </ToggleGroup>

    <!-- Viewer -->
    <div class="flex-1 overflow-hidden">
      <StitchMappingViewer v-if="mode === 'edit'" class="w-full h-full" />
      <StitchPreviewViewer v-else class="w-full h-full" />
    </div>
  </div>
</template>