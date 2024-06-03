<script setup lang="ts">
import { ContextualImage } from "@/lib/workspace";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Settings, Image, ImagePlus } from "lucide-vue-next";
import { ref, watch } from "vue";
import { deepClone } from "@/lib/utils";

const props = defineProps<{
  /**
   * Determines if this WorkspaceImageCard represents the base image.
   */
  base?: boolean;
}>();

const model = defineModel<ContextualImage>({ required: true });

/**
 * A local deeply cloned clone of the model.
 * Necessary to prevent constant reloads of the image viewer.
 */
const localModel = ref(deepClone(model.value));

/**
 * Update localModel with value from model when opened.
 */
const popoverOpen = ref(false);
watch(popoverOpen, (value) => {
  if (value) {
    localModel.value = deepClone(model.value);
  }
});

/**
 * Updates the workspace after pressing save in the popover.
 */
function updateModel() {
  model.value = deepClone(localModel.value);
  popoverOpen.value = false;
}
</script>

<template>
  <Card class="p-2">
    <div class="flex content-center justify-between">
      <div class="flex content-center space-x-2">
        <div class="aspect-square h-full p-1">
          <Image v-if="props.base" class="size-full" />
          <ImagePlus v-else class="size-full" />
        </div>
        <div class="whitespace-nowrap">
          <div>
            {{ model!.name }}
          </div>
          <div class="text-muted-foreground">
            {{ props.base ? "Base image" : "Contextual image" }}
          </div>
        </div>
      </div>
      <Popover v-model:open="popoverOpen">
        <PopoverTrigger as-child>
          <Button variant="ghost" class="size-8 p-2" title="Configure image">
            <Settings />
          </Button>
        </PopoverTrigger>
        <PopoverContent class="space-y-2">
          <div class="space-y-1">
            <Label for="name">Name</Label>
            <Input id="name" v-model="localModel.name" />
          </div>
          <div class="space-y-1">
            <Label for="image">Image location</Label>
            <Input id="image" v-model="localModel.imageLocation" />
          </div>
          <div class="space-y-1">
            <Label for="recipe">Recipe location</Label>
            <Input id="recipe" v-model="localModel.recipeLocation" />
          </div>
          <Button @click="updateModel">Save</Button>
        </PopoverContent>
      </Popover>
    </div>
  </Card>
</template>
