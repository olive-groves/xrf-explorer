<script setup lang="ts">
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { LabeledSlider } from "@/components/ui/slider";
import { Hand, Search, SquareMousePointer, Settings, LassoSelect } from "lucide-vue-next";
import { ToolState } from "./types";
import { FrontendConfig } from "@/lib/config";
import { inject } from "vue";

const config = inject<FrontendConfig>("config")!;

const state = defineModel<ToolState>("state", { required: true });
</script>

<template>
  <div
    class="absolute bottom-0 left-1/2 z-50 my-2 flex w-min -translate-x-1/2 space-x-1 rounded-md border bg-background
      p-1 shadow-sm"
  >
    <ToggleGroup type="single" v-model:model-value="state.tool">
      <ToggleGroupItem value="grab" class="size-8 p-2" title="Grab">
        <Hand />
      </ToggleGroupItem>
      <ToggleGroupItem value="lens" class="size-8 p-2" title="Lens">
        <Search />
      </ToggleGroupItem>
      <ToggleGroupItem value="rectangle" class="size-8 p-2" title="Rectangle selection">
        <SquareMousePointer />
      </ToggleGroupItem>
      <ToggleGroupItem value="lasso" class="size-8 p-2" title="Lasso selection">
        <LassoSelect />
      </ToggleGroupItem>
    </ToggleGroup>
    <Separator orientation="vertical" class="h-8" />
    <Popover>
      <PopoverTrigger as-child>
        <Button variant="ghost" class="size-8 p-2 hover:text-muted-foreground" title="Tool configuration">
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
