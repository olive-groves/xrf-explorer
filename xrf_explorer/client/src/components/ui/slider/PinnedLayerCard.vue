<script setup lang="ts">
import { PinnedSlider } from ".";
import { Eye, EyeOff, SlidersHorizontal, Pin } from "lucide-vue-next";
import { computed, ref, watch, WritableComputedRef } from "vue";
import {
  layerGroups,
  setLayerGroupIndex,
  setLayerGroupVisibility,
  setLayerGroupProperty,
} from "@/components/image-viewer/state";
import { LayerGroup } from "@/components/image-viewer/types";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { LabeledSlider } from "@/components/ui/slider";

const props = defineProps<{
  /**
   * The layer group associated with this card.
   */
  group: LayerGroup;
}>();

// Define emits
const emit = defineEmits<{
  (e: "unpin", group: LayerGroup): void;
}>();

// Computed reference to the layer group
const group = computed(() => props.group);

// Group list and number of pinned layers
const groups = ref<LayerGroup[]>([]);
const numberOfPinnedLayers = computed(() => groups.value.filter((g) => g.pinned).length);

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

// Computed proxies for easier access
const visible = computed({
  get: () => group.value.visible,
  set: (value: boolean) => {
    group.value.visible = value;
    setLayerGroupVisibility(group.value);
  },
});

const opacity = computed<number[]>({
  get: () => group.value.opacity,
  set: (value: number[]) => {
    group.value.opacity = value;
    setLayerGroupProperty(group.value, "opacityProperty");
  },
});

/**
 * Dynamic proxy for other properties.
 * @param prop - The property to create a proxy for.
 * @returns A computed proxy for the specified property.
 */
function proxyForProperty(prop: Property): WritableComputedRef<number[]> {
  return computed<number[]>({
    get: () => group.value[prop.nameRef] as number[],
    set: (value: number[]) => {
      (group.value[prop.nameRef] as number[]) = value;
      setLayerGroupProperty(group.value, prop.propertyName);
    },
  });
}

// Pre-build map of proxies for all properties
const propertyProxies: Record<string, WritableComputedRef<number[]>> = Object.fromEntries(
  properties.map((prop) => [prop.name, proxyForProperty(prop)]),
) as Record<string, WritableComputedRef<number[]>>;

/**
 * Toggles the pinned state of a layer group.
 */
function togglePin() {
  const group = props.group;

  if (!group.pinned) {
    // Trying to pin
    if (numberOfPinnedLayers.value >= 3) {
      alert("You can only pin up to 3 layers.");
      return;
    }
    // Pinning
    group.pinned = true;
    setLayerGroupProperty(group, "pinnedProperty");
  } else {
    // Unpinning
    group.pinned = false;
    setLayerGroupProperty(group, "pinnedProperty");
    emit("unpin", group);
  }
}
</script>

<template>
  <div class="w-[300px] rounded-md border border-border bg-card p-3 shadow-md">
    <div class="mb-2 flex items-center justify-between">
      <div class="font-medium">{{ props.group.name }}</div>
      <!-- All button at the right side of the header -->
      <div class="flex space-x-1">
        <!-- Pin button -->
        <Button
          variant="ghost"
          class="size-8 p-2"
          title="Unpin layer"
          @click="togglePin"
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
              v-model="propertyProxies[property.name].value"
            />
          </PopoverContent>
        </Popover>
        <!-- VISIBILITY TOGGLE -->
        <Button @click="visible = !visible" variant="ghost" class="size-8 p-2" title="Toggle visibility">
          <Eye v-if="group.visible" />
          <EyeOff v-else />
        </Button>
      </div>
    </div>
    <PinnedSlider v-model="opacity" :min="0" :max="1" :step="0.01" :default="[1]" />
  </div>
</template>
