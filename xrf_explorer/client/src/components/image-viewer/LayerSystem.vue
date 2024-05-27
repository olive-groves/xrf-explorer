<script setup lang="ts">
import { VueDraggableNext } from "vue-draggable-next";
import { Eye, EyeOff } from "lucide-vue-next";
import { ref, watch } from "vue";
import { layerGroups, setLayerGroupIndex, setLayerGroupVisibility, setLayerGroupProperty } from "./state";
import { LayerGroup, LayerVisibility } from "./types";

// Makes sure workspace.ts gets loaded
import "./workspace";

// Makes sure the workspace.ts file gets loaded
import "./workspace";
// import "./"

const groups = ref<LayerGroup[]>([]);

// Used for generalizing the code.
interface Property {
  name: string;
  max: number;
  propertyName: string;
  nameRef: keyof LayerGroup;
}

const properties: Property[] = [
  { name: "Opacity", max: 1, propertyName: "opacityProperty", nameRef: "opacity" },
  { name: "Contrast", max: 5, propertyName: "contrastProperty", nameRef: "contrast" },
  { name: "Saturation", max: 5, propertyName: "saturationProperty", nameRef: "saturation" },
];

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
    <!-- CREATES A CARD FOR EACH LAYER -->
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
        <!-- VISIBILITY TOGGLE -->
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
      <!-- SLIDERS FOR OPACITY, CONTRAST, AND SATURATION -->
      <div v-if="group.visible" class="space-y-2">
        <div class="flex items-center space-x-2" @click="() => checkedOutsideLens(group)">
          <Checkbox :checked="group.visibility == LayerVisibility.InsideLens" />
          <div class="whitespace-nowrap">Only visible inside of lens</div>
        </div>
        <div class="space-y-2" v-for="property in properties" :key="property.name">
          <div class="flex items-center justify-between">
            <div>{{ property.name }}</div>
            <div>{{ group[property.nameRef].toString() }}</div>
          </div>
          <Slider
            v-model="group[property.nameRef]"
            :min="0"
            :step="0.01"
            :max="property.max"
            class="pb-2"
            @update:model-value="() => setLayerGroupProperty(group, property.propertyName)"
          />
        </div>
      </div>
    </Card>
  </VueDraggableNext>
</template>
