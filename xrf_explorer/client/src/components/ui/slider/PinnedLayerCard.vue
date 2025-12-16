<script setup lang="ts">
import { PinnedSlider } from ".";
import { Eye, EyeOff, SlidersHorizontal, Pin, Search, SearchX } from "lucide-vue-next";
import { computed, ref, WritableComputedRef } from "vue";
import {
  layerGroups,
  setLayerGroupIndex,
  setLayerGroupVisibility,
  setLayerGroupProperty,
} from "@/components/image-viewer/state";
import { LayerGroup, LayerVisibility } from "@/components/image-viewer/types";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import {
  LabeledSlider,
  togglePin,
  checkedOutsideLens,
  mainProperties,
  properties,
  watchers,
} from "@/components/ui/slider";
import type { Property } from "@/components/ui/slider";

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

// Loads the layer groups into the LayerSystem.
// Updates the indices of the layers when the layers get reordered.
watchers(groupNames, layerGroups, groups, setLayerGroupIndex);

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
function SetTogglePin() {
  const group = props.group;
  group.pinned = togglePin(group, numberOfPinnedLayers.value);
  setLayerGroupProperty(group, "pinnedProperty");
  if (!group.pinned) {
    emit("unpin", group);
  }
}

/**
 * Toggle lens in a layer.
 * @param group The LayerGroup to toggle the lens of.
 */
function toggleLens(group: LayerGroup) {
  setCheckedOutsideLens(group);
}

/**
 * Updates the visibility of the layer group outside the lens.
 * @param group - The group to toggle and update.
 */
function setCheckedOutsideLens(group: LayerGroup) {
  checkedOutsideLens(group);
  setLayerGroupVisibility(group);
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
          @click="SetTogglePin"
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
