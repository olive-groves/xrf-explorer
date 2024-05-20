<script setup lang="ts">
import { VueDraggableNext } from "vue-draggable-next";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff } from "lucide-vue-next";
import { ref, watch } from "vue";

// Makes sure workspace.ts gets loaded
import "./workspace";
import { layerGroups, setLayerGroupIndex, setLayerGroupVisibility } from "./state";
import { LayerGroup, LayerVisibility } from "./types";

const groups = ref<LayerGroup[]>([]);

watch(
  layerGroups,
  (newGroups) => {
    groups.value = Object.keys(newGroups).map((key) => newGroups[key]);
  },
  { immediate: true },
);

watch(groups, (newOrder) => {
  newOrder.forEach((layer, index) => {
    setLayerGroupIndex(layer, index);
  });
});

/**
 *
 * @param value
 * @param group
 */
function checkedInsideLens(group: LayerGroup) {
  if (group.visibility == LayerVisibility.Invisible) {
    group.visibility = LayerVisibility.InsideLens;
  } else if (group.visibility == LayerVisibility.Visible) {
    group.visibility = LayerVisibility.OutsideLens;
  } else if (group.visibility == LayerVisibility.InsideLens) {
    group.visibility = LayerVisibility.Invisible;
  } else if (group.visibility == LayerVisibility.OutsideLens) {
    group.visibility = LayerVisibility.Visible;
  }
  setLayerGroupVisibility(group);
}

/**
 *
 * @param value
 * @param group
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
  <VueDraggableNext class="space-y-2" v-model="groups" @change="console.log">
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
      <div v-if="group.visible" class="space-y-1">
        <div class="flex items-center space-x-2">
          <Checkbox
            @update:checked="() => checkedInsideLens(group)"
            :checked="group.visibility == LayerVisibility.Visible || group.visibility == LayerVisibility.InsideLens"
          />
          <div>Visible inside of lens</div>
        </div>
        <div class="flex items-center space-x-2">
          <Checkbox
            @update:checked="() => checkedOutsideLens(group)"
            :checked="group.visibility == LayerVisibility.Visible || group.visibility == LayerVisibility.OutsideLens"
          />
          <div>Visible outside of lens</div>
        </div>
      </div>
    </Card>
  </VueDraggableNext>
</template>
