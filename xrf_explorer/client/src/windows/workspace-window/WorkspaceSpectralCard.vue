<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { SpectralCube } from "@/lib/workspace";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { AudioWaveform, Settings } from "lucide-vue-next";
import { ref, watch } from "vue";
import { deepClone } from "@/lib/utils";

const model = defineModel<SpectralCube>();

/**
 * A local deeply cloned clone of the model.
 * Necessary to prevent constant reloads of the image viewer.
 */
let localModel = deepClone(model.value!);

/**
 * Update localModel with value from model when opened.
 */
const popoverOpen = ref(false);
watch(popoverOpen, (value) => {
  if (value) {
    localModel = deepClone(model.value!);
  }
});

/**
 * Updates the contextual image after pressing save in the popover.
 */
function updateImage() {
  model.value = deepClone(localModel);
  popoverOpen.value = false;
}
</script>

<template>
  <Card class="p-2">
    <div class="flex content-center justify-between">
      <div class="flex content-center space-x-2">
        <div class="aspect-square h-full p-1">
          <AudioWaveform class="size-full" />
        </div>
        <div class="whitespace-nowrap">
          <div>
            {{ model!.name }}
          </div>
          <div class="text-muted-foreground">Spectral datacube</div>
        </div>
      </div>
      <Popover v-model:open="popoverOpen">
        <PopoverTrigger as-child>
          <Button variant="ghost" class="size-8 p-2">
            <Settings />
          </Button>
        </PopoverTrigger>
        <PopoverContent class="space-y-2">
          <div class="space-y-1">
            <Label for="name">Name</Label>
            <Input id="name" v-model="localModel.name" />
          </div>
          <div class="space-y-1">
            <Label for="raw">RAW location</Label>
            <Input id="raw" v-model="localModel.rawLocation" />
          </div>
          <div class="space-y-1">
            <Label for="rpl">RPL location</Label>
            <Input id="rpl" v-model="localModel.rplLocation" />
          </div>
          <div class="space-y-1">
            <Label for="recipe">Recipe location</Label>
            <Input id="recipe" v-model="localModel.recipeLocation" />
          </div>
          <Button @click="updateImage">Save</Button>
        </PopoverContent>
      </Popover>
    </div>
  </Card>
</template>
