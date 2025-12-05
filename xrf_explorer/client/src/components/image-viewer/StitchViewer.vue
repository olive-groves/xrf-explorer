<script lang="ts">
import { ref } from 'vue';
import StitchMappingViewer from './StitchMappingViewer.vue';
import StitchPreviewViewer from './StitchPreviewViewer.vue';
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { canPreview } from './stitchPoints';

export default {
  name: 'StitchViewer',
  components: { StitchMappingViewer, StitchPreviewViewer, ToggleGroup, ToggleGroupItem },
  setup() {
    const mode = ref<'edit' | 'preview'>('edit');

    return { mode, canPreview };
  }
};
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Toggle Button -->
    <ToggleGroup type="single" v-model="mode" class="space-x-2 mb-2">
      <ToggleGroupItem value="edit" variant="outline">Edit</ToggleGroupItem>
      <div :title="!canPreview ? 'Can only preview after mapping 4 points for each greyscale' : ''">
        <ToggleGroupItem
          value="preview"
          variant="outline"
        >
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