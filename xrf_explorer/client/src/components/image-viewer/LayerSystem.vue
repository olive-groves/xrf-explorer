<script setup lang="ts">
import { VueDraggableNext } from "vue-draggable-next";
import { Eye, EyeOff, Search, SearchX, SlidersHorizontal, ListRestart, Pin } from "lucide-vue-next";
import { computed, ref } from "vue";
import {
  layerGroups,
  setLayerGroupIndex,
  setLayerGroupVisibility,
  setLayerGroupProperty,
  updateLayerGroupLayers,
} from "./state";
import { LayerGroup, LayerVisibility } from "./types";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import {
  LabeledSlider,
  togglePin,
  checkedOutsideLens,
  mainProperties,
  properties,
  watchers,
} from "@/components/ui/slider";

// Makes sure workspace.ts gets loaded
import "./workspace";

const groups = ref<LayerGroup[]>([]);
const numberOfPinnedLayers = computed(() => groups.value.filter((g) => g.pinned).length);

const groupNames = computed(() => Object.keys(layerGroups.value));

// Loads the layer groups into the LayerSystem.
// Updates the indices of the layers when the layers get reordered.
watchers(groupNames, layerGroups, groups, setLayerGroupIndex);

/**
 * Toggle lens in a layer.
 * @param group The LayerGroup to toggle the lens of.
 */
function toggleLens(group: LayerGroup) {
  checkedOutsideLens(group);
  setLayerGroupVisibility(group);
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
            @click="group.pinned = togglePin(group, numberOfPinnedLayers)"
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
