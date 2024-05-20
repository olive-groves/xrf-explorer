<script setup lang="ts">
import { VueDraggableNext } from "vue-draggable-next";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Eye, EyeOff } from "lucide-vue-next";
import { ref, watch } from "vue";

// Makes sure workspace.ts gets loaded
import "./workspace";
import { layerGroups, setLayerGroupIndex, setLayerGroupVisibility } from "./state";
import { LayerGroup } from "./types";

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
    </Card>
  </VueDraggableNext>
</template>
