<script setup lang="ts">
import { VueDraggableNext } from "vue-draggable-next";
import { Eye, EyeOff } from "lucide-vue-next";
import { ref, watch } from "vue";

// Makes sure workspace.ts gets loaded
import "./workspace";
import { layerGroups, setLayerGroupIndex, setLayerGroupOpacity, setLayerGroupContrast, setLayerGroupSaturation, setLayerGroupVisibility } from "./state";
import { LayerGroup, LayerVisibility } from "./types";

const groups = ref<LayerGroup[]>([]);

/**
 * Loads the layer groups into the LayerSystem.
 */
watch(
  layerGroups,
  (newGroups) => {
    groups.value = Object.keys(newGroups)
      .map((key) => newGroups[key])
      .sort((a, b) => a.index - b.index);
  },
  { immediate: true },
);

/**
 * Updates the indices of the layers when the layers get reordered.
 */
watch(
  groups,
  (newOrder) => {
    newOrder.forEach((layer, index) => {
      layer.index = index;
      setLayerGroupIndex(layer);
    });
  },
  { immediate: true },
);

/**
 * Updates the visibility of the layer group outside of the lens.
 * @param group - The group to toggle and update.
 */
function checkedOutsideLens(group: LayerGroup) {
  if (group.visibility == LayerVisibility.Invisible) {
    group.visibility = LayerVisibility.OutsideLens;
  } else if (group.visibility == LayerVisibility.Visible) {
    group.visibility = LayerVisibility.InsideLens;
  } else if (group.visibility == LayerVisibility.InsideLens) {
    group.visibility = LayerVisibility.Visible;
  } else if (group.visibility == LayerVisibility.OutsideLens) {
    group.visibility = LayerVisibility.Invisible;
  }
  setLayerGroupVisibility(group);
}
</script>

<template>
  <VueDraggableNext class="space-y-2" v-model="groups">
    <Card v-for="group in groups" :key="group.name" class="space-y-2 p-2">
      <div class="flex justify-between">
        <div>
          <div>
            {{ group.name }}
          </div>
          <div class="whitespace-nowrap text-muted-foreground">
            {{ group.description }}
          </div>
        </div>
        <Button
          @click="
            group.visible = !group.visible;
            setLayerGroupVisibility(group);
          "
          variant="ghost"
          class="size-8 p-2"
          title="Toggle visibility"
        >
          <Eye v-if="group.visible" />
          <EyeOff v-else />
        </Button>
      </div>
      <div v-if="group.visible" class="space-y-2">
        <div class="flex items-center space-x-2" @click="() => checkedOutsideLens(group)">
          <Checkbox :checked="group.visibility == LayerVisibility.InsideLens" />
          <div class="whitespace-nowrap">Only visible inside of lens</div>
        </div>
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <div>Opacity</div>
            <div>{{ group.opacity[0] }}</div>
          </div>
          <Slider
            v-model="group.opacity"
            :min="0"
            :step="0.01"
            :max="1"
            class="pb-2"
            @update:model-value="() => setLayerGroupOpacity(group)"
          />
        </div>
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <div>Contrast</div>
            <div>{{ group.contrast[0] }}</div>
          </div>
          <Slider
            v-model="group.contrast"
            :min="0"
            :step="0.01"
            :max="5"
            class="pb-2"
            @update:model-value="() => setLayerGroupContrast(group)"
          />
        </div>
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <div>Saturation</div>
            <div>{{ group.saturation[0] }}</div>
          </div>
          <Slider
            v-model="group.saturation"
            :min="0"
            :step="0.01"
            :max="5"
            class="pb-2"
            @update:model-value="() => setLayerGroupSaturation(group)"
          />
        </div>
      </div>
    </Card>
  </VueDraggableNext>
</template>
