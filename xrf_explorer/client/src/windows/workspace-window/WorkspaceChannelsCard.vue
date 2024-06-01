<script setup lang="ts">
import { Checkbox } from "@/components/ui/checkbox";
import { ElementalChannel } from "@/lib/workspace";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Layers3, Settings } from "lucide-vue-next";
import { ref, watch } from "vue";
import { deepClone } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";

const model = defineModel<ElementalChannel[]>({ required: true });

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
          <Layers3 class="size-full" />
        </div>
        <div class="whitespace-nowrap">
          <div>Elemental channels</div>
          <div class="text-muted-foreground">Generated data</div>
        </div>
      </div>
      <Popover v-model:open="popoverOpen">
        <PopoverTrigger as-child>
          <Button variant="ghost" class="size-8 p-2" title="Configure elemental cube">
            <Settings />
          </Button>
        </PopoverTrigger>
        <PopoverContent class="space-y-2">
          <ScrollArea class="h-64">
            <div class="grid grid-cols-[min-content,min-content,1fr] grid-rows-[repeat(2.25rem)] gap-2">
              <template v-for="channel in localModel" :key="channel.channel">
                <div class="flex justify-end text-muted-foreground">
                  <div v-text="channel.channel" class="h-min self-center" />
                </div>
                <Checkbox v-model:checked="channel.enabled" class="my-2.5 size-4" />
                <Input v-model="channel.name" />
              </template>
            </div>
          </ScrollArea>
          <Button @click="updateModel">Save</Button>
        </PopoverContent>
      </Popover>
    </div>
  </Card>
</template>
