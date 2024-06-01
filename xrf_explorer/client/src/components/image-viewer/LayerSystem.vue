<script setup lang="ts">
import { VueDraggableNext } from "vue-draggable-next";
import { Eye, EyeOff, SlidersHorizontal } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import { layerGroups, setLayerGroupIndex, setLayerGroupVisibility, setLayerGroupProperty } from "./state";
import { LayerGroup, LayerVisibility } from "./types";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { LabeledSlider } from "@/components/ui/slider";

// Makes sure workspace.ts gets loaded
import "./workspace";

const groups = ref<LayerGroup[]>([]);

// Used for generalizing the code.
interface Property {
  name: string;
  min: number;
  max: number;
  default: number;
  propertyName: string;
  nameRef: keyof LayerGroup;
}

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
        <div>
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
                v-model="group[property.nameRef]"
                :min="property.min"
                :max="property.max"
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
        <!-- VISIBILITY CHECKBOX -->
        <div class="flex items-center space-x-2" @click="() => checkedOutsideLens(group)">
          <Checkbox :checked="group.visibility == LayerVisibility.InsideLens" />
          <div class="whitespace-nowrap">Only visible inside of lens</div>
        </div>

        <!-- SLIDERS FOR ALL MAIN PROPERTIES -->
        <LabeledSlider
          v-for="property in properties.filter((prop) => mainProperties.includes(prop.name))"
          :key="property.name"
          :label="property.name"
          v-model="group[property.nameRef]"
          :min="property.min"
          :max="property.max"
          @update="() => setLayerGroupProperty(group, property.propertyName)"
        />
      </div>
    </Card>
  </VueDraggableNext>
</template>
