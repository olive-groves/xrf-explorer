<script setup lang="ts">
import { VueDraggableNext } from "vue-draggable-next";
import { Eye, EyeOff, Search, SearchX, SlidersHorizontal, ListRestart, Pin } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import {
  layerGroups,
  setLayerGroupIndex,
  setLayerGroupVisibility,
  setLayerGroupProperty,
  updateLayerGroupLayers,
} from "./state";
import { LayerGroup, LayerVisibility } from "./types";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { LabeledSlider } from "@/components/ui/slider";

// Makes sure workspace.ts gets loaded
import "./workspace";

const groups = ref<LayerGroup[]>([]);
const numberOfPinnedLayers = computed(() => groups.value.filter((g) => g.pinned).length);

// Used for generalizing the code.
interface Property {
  name: string;
  min: number;
  max: number;
  default: number;
  propertyName: string;
  nameRef: keyof LayerGroup;
}

// Adjustable properties of each layer group.
// Main properties are always directly visible in the Layer System,
// all other properties are placed in a separate popover.
const mainProperties = ["Opacity"];
const properties: Property[] = [
  { name: "Opacity", min: 0, max: 1, default: 1, propertyName: "opacityProperty", nameRef: "opacity" },
  { name: "Contrast", min: 0, max: 5, default: 1, propertyName: "contrastProperty", nameRef: "contrast" },
  { name: "Saturation", min: 0, max: 5, default: 1, propertyName: "saturationProperty", nameRef: "saturation" },
  { name: "Gamma", min: 0, max: 5, default: 1, propertyName: "gammaProperty", nameRef: "gamma" },
  { name: "Brightness", min: -1, max: 1, default: 0, propertyName: "brightnessProperty", nameRef: "brightness" },
];

const groupNames = computed(() => Object.keys(layerGroups.value));

/**
 * Loads the layer groups into the LayerSystem.
 */
watch(
  groupNames,
  (newGroups) => {
    groups.value = newGroups.map((name) => layerGroups.value[name]).sort((a, b) => a.index - b.index);
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
 * Updates the visibility of the layer group outside the lens.
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

/**
 * Toggles the pinned state of a layer group.
 * @param group - The layer group to toggle the pinned state of.
 */
function togglePin(group: LayerGroup) {
  if (!group.pinned) {
    // Trying to pin
    if (numberOfPinnedLayers.value >= 3) {
      alert("You can only pin up to 3 layers.");
      return;
    }
    group.pinned = true;
  } else {
    // Unpinning
    group.pinned = false;
  }
}

/**
 * Toggle lens in a layer.
 * @param group The LayerGroup to toggle the lens of.
 */
function toggleLens(group: LayerGroup) {
  checkedOutsideLens(group);
}

/**
 * Reset all sliders to default values.
 */
function resetSliders() {
  //loop through al groups
  for (const group in groups.value) {
    groups.value[group].visible = groups.value[group].default_visibility;
    groups.value[group].visibility = LayerVisibility.Visible;

    //Loop through all the properties in the group and reset to default
    for (const property in properties) {
      const propertyName = properties[property].nameRef;

      (groups.value[group][propertyName] as number[])[0] = properties[property].default;
    }

    updateLayerGroupLayers(groups.value[group]);
  }
}
</script>

<template>
  <VueDraggableNext class="space-y-2" v-model="groups">
    <Button class="basis-1/2" variant="outline" @click="resetSliders()" title="Reset layer settings"
      ><ListRestart class="size-4" />
    </Button>
    <!-- CREATES A CARD FOR EACH LAYER -->
    <Card v-for="group in groups" :key="group.name" class="cursor-move space-y-2 p-2">
      <div class="flex justify-between">
        <div>
          <div>
            {{ group.name }}
          </div>
        </div>
        <div>
          <!-- Pin button -->
          <Button
            variant="ghost"
            class="size-8 p-2"
            :title="group.pinned ? 'Unpin layer' : 'Pin layer'"
            @click="togglePin(group)"
            :disabled="!group.pinned && numberOfPinnedLayers >= 3"
          >
            <Pin :class="group.pinned ? 'text-primary' : 'text-muted-foreground'" class="size-5" />
          </Button>

          <!-- SLIDERS POPOVER -->
          <Popover v-if="group.visible">
            <PopoverTrigger>
              <Button variant="ghost" class="size-8 p-2" title="Only visible inside lens" @click="toggleLens(group)">
                <SearchX v-if="group.visibility == LayerVisibility.InsideLens" />
                <Search v-else />
              </Button>
            </PopoverTrigger>
          </Popover>
          <Popover v-if="group.visible">
            <PopoverTrigger>
              <Button variant="ghost" class="size-8 p-2" title="Additional sliders">
                <SlidersHorizontal />
              </Button>
            </PopoverTrigger>
            <PopoverContent>
              <!-- SLIDERS FOR ALL NON-MAIN PROPERTIES -->
              <LabeledSlider
                v-for="property in properties.filter((prop) => !mainProperties.includes(prop.name))"
                :key="property.name"
                :label="property.name"
                :min="property.min"
                :max="property.max"
                :default="[property.default]"
                v-model="group[property.nameRef] as any"
                @update="() => setLayerGroupProperty(group, property.propertyName)"
              />
            </PopoverContent>
          </Popover>
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
      </div>
      <div v-if="group.visible" class="space-y-2">
        <!-- SLIDERS FOR ALL MAIN PROPERTIES -->
        <LabeledSlider
          v-for="property in properties.filter((prop) => mainProperties.includes(prop.name))"
          :key="property.name"
          :label="property.min.toString()"
          v-model="group[property.nameRef] as any"
          :min="property.min"
          :max="property.max"
          :default="[property.default]"
          @update="() => setLayerGroupProperty(group, property.propertyName)"
          :title="property.name"
        />
      </div>
    </Card>
  </VueDraggableNext>
</template>
