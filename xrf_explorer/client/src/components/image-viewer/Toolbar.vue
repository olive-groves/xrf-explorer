<script setup lang="ts">
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { LabeledSlider } from "@/components/ui/slider";
import { Hand, Search, SquareMousePointer, Settings, LassoSelect, Fullscreen, SearchX } from "lucide-vue-next";
import { Tool, ToolState } from "./types";
import { FrontendConfig } from "@/lib/config";
import { inject, defineEmits } from "vue";

const config = inject<FrontendConfig>("config")!;

const state = defineModel<ToolState>("state", { required: true });
const emit = defineEmits(["reset-viewport", "clear-selection"]);

const resetViewport = () => {
  // Emit reset viewport message to imageViewer
  emit("reset-viewport");
};
</script>

<template>
  <div
    class="absolute bottom-0 left-1/2 z-50 my-2 flex w-min -translate-x-1/2 cursor-default space-x-1 rounded-md border
      bg-background p-1 shadow-sm"
  >
    <ToggleGroup type="single" v-model:model-value="state.tool">
      <ToggleGroupItem :value="Tool.Grab" class="size-8 p-2" title="Grab">
        <Hand />
      </ToggleGroupItem>
      <ToggleGroupItem :value="Tool.Lens" class="size-8 p-2" title="Lens">
        <Search />
      </ToggleGroupItem>
      <ToggleGroupItem :value="Tool.Rectangle" class="size-8 p-2" title="Rectangle selection">
        <SquareMousePointer />
      </ToggleGroupItem>
      <ToggleGroupItem :value="Tool.Polygon" class="size-8 p-2" title="Polygon selection">
        <LassoSelect />
      </ToggleGroupItem>
    </ToggleGroup>
    <Separator orientation="vertical" class="h-8" />
    <Button variant="ghost" class="size-8 p-2" title="Cancel selection" @click="emit('clear-selection')">
      <SearchX />
    </Button>
    <Button variant="ghost" class="size-8 p-2" title="Reset painting location" @click="resetViewport">
      <Fullscreen />
    </Button>
    <Separator orientation="vertical" class="h-8" />
    <Popover>
      <PopoverTrigger as-child>
        <Button variant="ghost" class="size-8 p-2" title="Tool configuration">
          <Settings />
        </Button>
      </PopoverTrigger>
      <PopoverContent class="m-2 w-60 space-y-2">
        <LabeledSlider
          label="Movement speed"
          :min="0.1"
          :max="3.0"
          :step="0.1"
          :default="[config.imageViewer.defaultMovementSpeed]"
          v-model="state.movementSpeed"
        />
        <LabeledSlider
          label="Scroll speed"
          :min="0.1"
          :max="3.0"
          :step="0.1"
          :default="[config.imageViewer.defaultScrollSpeed]"
          v-model="state.scrollSpeed"
        />
        <LabeledSlider
          label="Lens size"
          :min="1"
          :max="400"
          :step="1"
          unit="px"
          :default="[config.imageViewer.defaultLensSize]"
          v-model="state.lensSize"
        />
      </PopoverContent>
    </Popover>
  </div>
</template>
