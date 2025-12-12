<script setup lang="ts">
// Import the necessary functions and components
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Popover, PopoverAnchor, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { LabeledSlider } from "@/components/ui/slider";
import {
  NumberField,
  NumberFieldContent,
  NumberFieldInput,
} from "@/components/ui/number-field";
// Import the necessary icons
import { Hand, Search, SquareMousePointer, Settings, LassoSelect, Fullscreen, SquareX } from "lucide-vue-next";
import { Tool, ToolState } from "./types";
import { FrontendConfig } from "@/lib/config";
import { inject } from "vue";
import Label from "../ui/label/Label.vue";
import { appState } from "@/lib/appState";
import { computed, ref } from "vue";
import { Point2D } from "@/lib/utils";
import { getSystemErrorMap } from "util";
import { SelectionAreaType } from "@/lib/selection";

// Inject the configuration
const config = inject<FrontendConfig>("config")!;

// Define the model and emits
const state = defineModel<ToolState>("state", { required: true });
const emit = defineEmits(["resetViewport", "clearSelection"]);

const isOpen = ref(false);

const points = computed({
  get() {
    // Ensure the container exists
    console.log("HEREGET");
    if (!appState.selection.imageViewer) {
      appState.selection.imageViewer = { type: SelectionAreaType.Rectangle, points: [] };
    }

    // Ensure the array exists
    const p = appState.selection.imageViewer.points;

    // Ensure at least two points
    if (!p[0]) p[0] = { x: 0, y: 0 };
    if (!p[1]) p[1] = { x: 0, y: 0 };

    return p;
  },

  set(v) {
    appState.selection.imageViewer = { type: SelectionAreaType.Rectangle, points: v };
  }
});

function handleDblClick() {
  isOpen.value = true;

  console.log(isOpen.value);
}

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
      <Popover v-model:open="isOpen">
        <PopoverAnchor>
          <ToggleGroupItem :value="Tool.Rectangle" class="size-8 p-2" title="Rectangle selection" @dblclick.stop="handleDblClick">
            <SquareMousePointer />
          </ToggleGroupItem>
        </PopoverAnchor>
        <PopoverContent class="m-2 space-y-2">
          <Label>Coordinates</Label>
            <div class="grid grid-cols-2 gap-2">
              <!-- Top-left X -->
              <NumberField
                v-model="points[0].x"
                @input="(v: { target: { value: any; }; }) => points = points.map((p, i) => i === 0 ? {...p, x: Number(v.target.value)} : p)"
                :min="0"
                :max="99999"
                :step="1"
                title="Top left x coordinate"
                id="tlx"
                :format-options="{
                  minimumIntegerDigits: 1,
                  maximumFractionDigits: 0,
                }"
              >
                <NumberFieldContent class="h-8 px-1.5">
                  <NumberFieldInput/>
                </NumberFieldContent>
              </NumberField>

              <!-- Top-left Y -->
              <NumberField
                v-model="points[0].y"
                @input="(v: { target: { value: any; }; }) => points = points.map((p, i) => i === 0 ? {...p, y: Number(v.target.value)} : p)"
                :min="0"
                :max="99999"
                :step="1"
                id="tly"
                :format-options="{
                  minimumIntegerDigits: 1,
                  maximumFractionDigits: 0,
                }"
              >
                <NumberFieldContent class="h-8 px-1.5">
                  <NumberFieldInput/>
                </NumberFieldContent>
              </NumberField>

              <!-- Bottom-right X -->
              <NumberField
                v-model="points[1].x"
                @input="(v: { target: { value: any; }; }) => points = points.map((p, i) => i === 1 ? {...p, x: Number(v.target.value)} : p)"
                :min="0"
                :max="99999"
                :step="1"
                id="brx"
                :format-options="{
                  minimumIntegerDigits: 1,
                  maximumFractionDigits: 0,
                }"
              >
                <NumberFieldContent class="h-8 px-1.5">
                  <NumberFieldInput/>
                </NumberFieldContent>
              </NumberField>

              <!-- Bottom-right Y -->
              <NumberField
                v-model="points[1].y"
                @input="(v: { target: { value: any; }; }) => points = points.map((p, i) => i === 1 ? {...p, y: Number(v.target.value)} : p)"
                :min="0"
                :max="99999"
                :step="1"
                id="bry"
                :format-options="{
                  minimumIntegerDigits: 1,
                  maximumFractionDigits: 0,
                }"
              >
                <NumberFieldContent class="h-8 px-1.5">
                  <NumberFieldInput/>
                </NumberFieldContent>
              </NumberField>
            </div>
        </PopoverContent>
      </Popover>
      <ToggleGroupItem :value="Tool.Polygon" class="size-8 p-2" title="Polygon selection">
        <LassoSelect />
      </ToggleGroupItem>
    </ToggleGroup>
    <Separator orientation="vertical" class="h-8" />
    <Button variant="ghost" class="size-8 p-2" title="Clear selection" @click="emit('clearSelection')">
      <SquareX />
    </Button>
    <Button variant="ghost" class="size-8 p-2" title="Reset painting location" @click="emit('resetViewport')">
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
