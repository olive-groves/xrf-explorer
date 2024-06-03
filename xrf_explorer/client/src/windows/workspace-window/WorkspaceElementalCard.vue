<script setup lang="ts">
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { ElementalCube, ElementalCubeFileType } from "@/lib/workspace";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Atom, Settings } from "lucide-vue-next";
import { ref, watch } from "vue";
import { deepClone } from "@/lib/utils";

const model = defineModel<ElementalCube>({ required: true });

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
          <Atom class="size-full" />
        </div>
        <div class="whitespace-nowrap">
          <div>
            {{ model.name }}
          </div>
          <div class="text-muted-foreground">Elemental datacube</div>
        </div>
      </div>
      <Popover v-model:open="popoverOpen">
        <PopoverTrigger as-child>
          <Button variant="ghost" class="size-8 p-2" title="Configure elemental cube">
            <Settings />
          </Button>
        </PopoverTrigger>
        <PopoverContent class="space-y-2">
          <div class="space-y-1">
            <Label for="name">Name</Label>
            <Input id="name" v-model="localModel.name" />
          </div>
          <div class="space-y-1">
            <div>Filetype</div>
            <RadioGroup
              :default-value="localModel.fileType"
              @update:model-value="(value) => (localModel.fileType = value as ElementalCubeFileType)"
            >
              <div class="flex items-center space-x-2">
                <RadioGroupItem id="csv" value="csv" />
                <Label for="csv">.csv file</Label>
              </div>
              <div class="flex items-center space-x-2">
                <RadioGroupItem id="dms" value="dms" />
                <Label for="dms">.dms file</Label>
              </div>
            </RadioGroup>
          </div>
          <div class="space-y-1">
            <Label for="data">Datacube location</Label>
            <Input id="data" v-model="localModel.dataLocation" />
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
