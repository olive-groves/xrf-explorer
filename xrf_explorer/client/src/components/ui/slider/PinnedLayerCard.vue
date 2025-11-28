<script setup lang="ts">
import { PinnedSlider } from ".";
import { Eye, EyeOff, SlidersHorizontal, Pin } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import {
  layerGroups,
  setLayerGroupIndex,
  setLayerGroupVisibility,
  setLayerGroupProperty,
} from "@/components/image-viewer/state";
import { LayerGroup } from "@/components/image-viewer/types";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { LabeledSlider } from "@/components/ui/slider";
import { emit } from "process";

const props = defineProps<{
  group: LayerGroup;
}>();

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

const emit = defineEmits<{
  (e: "unpin", group: LayerGroup): void;
}>();

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
    emit("unpin", group);
  }
}
</script>

<template>
  <div class="w-[300px] rounded-md border border-border bg-card p-3 shadow-md">
    <div class="mb-2 flex items-center justify-between">
      <div class="font-medium">{{ group.name }}</div>
      <!-- All button at the right side of the header -->
      <div class="flex space-x-1">
        <!-- Pin button -->
        <Button
          variant="ghost"
          class="size-8 p-2"
          title="Unpin layer"
          @click="togglePin(group)"
          :disabled="!group.pinned && numberOfPinnedLayers >= 3"
        >
          <Pin :class="group.pinned ? 'text-primary' : 'text-muted-foreground'" class="size-5" />
        </Button>
        <!-- SLIDERS POPOVER -->
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
              v-model="group[property.nameRef]"
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
    <PinnedSlider
      v-model="group.opacity"
      :min="0"
      :max="1"
      :step="0.01"
      :value="group.opacity"
      :default="[1]"
      @update="() => setLayerGroupProperty(props.group, 'opacityProperty')"
    />
  </div>
</template>
