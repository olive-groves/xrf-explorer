<script setup lang="ts">
import { Stitchbar } from "@/components/image-viewer";
import { computed, inject, onBeforeUnmount, ref, onMounted } from "vue";
import { StitchTool, StitchState } from "./types";
import { useElementBounding } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { getTargetSize } from "./api";
import { toast } from "vue-sonner";
import { SelectionAreaType } from "@/lib/selection";
import arrowImg from "./img1.jpg";
import { on } from "events";

const config = inject<FrontendConfig>("config")!;

const glcontainer = ref<HTMLDivElement | null>(null);
const glcanvas = ref<HTMLCanvasElement | null>(null);

const viewport: {
  center: { x: number; y: number };
  zoom: number;
} = {
  center: { x: 0, y: 0 },
  zoom: 0,
};

const stitchState = ref<StitchState>({
  tool: StitchTool.Grab,
  movementSpeed: [config.imageViewer.defaultMovementSpeed],
  scrollSpeed: [config.imageViewer.defaultScrollSpeed],
  lensSize: [config.imageViewer.defaultLensSize],
});

const selectionToolActive = computed(() =>
  Object.values(SelectionAreaType as { [key: string]: string }).includes(stitchState.value.tool as string),
);

const canvasSize = useElementBounding(glcontainer);
const width = canvasSize.width;
const height = canvasSize.height;

// Flag to prevent the zoom limit toast from being shown multiple times
let zoomLimitReached = false;

// Dummy image boxes
interface ImageBox {
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
}

const dummyImages = ref<ImageBox[]>([
  { x: 80, y: 80, width: 300, height: 225, rotation: 0 },
  { x: 250, y: 100, width: 300, height: 225, rotation: 0 },
  { x: 100, y: 300, width: 300, height: 225, rotation: 0 },
  { x: 400, y: 220, width: 300, height: 225, rotation: 0 },
]);
const selectedIdx = ref(0);
const selectedImage = computed(() => dummyImages.value[selectedIdx.value]);

const draggingIndex = ref<number | null>(null);
const dragOffset = ref({ x: 0, y: 0 });

onMounted(() => {
  window.addEventListener("keydown", onKeyDown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeyDown);
});

function startDrag(index: number, e: MouseEvent) {
  // Only allow dragging when using Grab tool
  if (stitchState.value.tool !== StitchTool.Grab) return;
  draggingIndex.value = index;
  const img = dummyImages.value[index];
  const rect = glcontainer.value?.getBoundingClientRect();
  if (!rect) return;

  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  dragOffset.value = {
    x: mouseX - img.x,
    y: mouseY - img.y
  };
}

function rotateBox(index: number) {
  const img = dummyImages.value[index];
  img.rotation = (img.rotation + 90) % 360;
}


function onImageMouseMove(e: MouseEvent) {
  const rect = glcontainer.value?.getBoundingClientRect();
  if (!rect) return;

  // Dragging
  if (draggingIndex.value !== null) {
    const img = dummyImages.value[draggingIndex.value];
    img.x = e.clientX - rect.left - dragOffset.value.x;
    img.y = e.clientY - rect.top - dragOffset.value.y;
  }
}

function stopInteractions() {
  draggingIndex.value = null;
}

/**
 * Resets the viewport to a home position such that the entire painting is visible.
 */
async function resetViewport() {
  const size = await getTargetSize();
  const fill = 0.9;
  viewport.center.x = size.width / 2;
  viewport.center.y = size.height / 2;
  viewport.zoom = Math.max(Math.log(size.width / width.value / fill), Math.log(size.height / height.value / fill));
  
}

const dragging = ref(false);

/**
 * Event handler for the onClick event on the glcanvas.
 * @param event - The mouse event.
 */
function onClick(event: MouseEvent) {
  if (event.button == 2) {
    // Prevent opening of context menu.
    event.preventDefault();
  }
}

/**
 * Event handler for the onMouseDown event on the glcanvas.
 * @param event - The mouse event.
 */
function onMouseDown(event: MouseEvent, index: number) {
  if (event.button == 0) {
    startDrag(index, event);
  } else if (event.button == 2) {
    rotateBox(index);
    event.preventDefault();
  }
  selectedIdx.value = index
}

/**
 * Event handler for the onMouseUp event on the glcanvas.
 * @param event - The mouse event.
 */
function onMouseUp(event: MouseEvent) {
  if (event.button == 0) {
    dragging.value = false;
  } else if (event.button == 2 && selectionToolActive.value) {
    dragging.value = false;
  }
}

/**
 * Event handler for the onMouseLeave event on the glcanvas.
 */
function onMouseLeave() {
  dragging.value = false;
}

/**
 * Event handler for the onMouseMove event on the glcanvas.
 * Modifies the viewport if the mouse is pressed down.
 * @param event The event containing the movement of the mouse.
 */
function onMouseMove(event: MouseEvent) {
  if (dragging.value) {
    const scale = Math.exp(viewport.zoom) * stitchState.value.movementSpeed[0];
    viewport.center.x -= event.movementX * scale;
    viewport.center.y += event.movementY * scale;
  }
}

/**
 * Event handler for the onWheel event on the glcanvas.
 * Modifies the viewport to allow zooming in and out on the painting.
 * The zoom gets clamped to a reasonable range.
 * @param event The wheel event containing the amount that was scrolled.
 */
function onWheel(event: WheelEvent) {
  viewport.zoom += (event.deltaY / 500.0) * stitchState.value.scrollSpeed[0];

  // Clamp zoom to a reasonable range
  if (viewport.zoom >= config.imageViewer.zoomLimit || viewport.zoom <= -config.imageViewer.zoomLimit) {
    viewport.zoom = Math.min(config.imageViewer.zoomLimit, Math.max(-config.imageViewer.zoomLimit, viewport.zoom));
    if (!zoomLimitReached) {
      toast.info("Zoom limit reached");
      // Prevent the toast from being shown multiple times
      zoomLimitReached = true;
    }
  } else {
    zoomLimitReached = false;
  }
}

// Move the images using arrow keys
function onKeyDown(event: KeyboardEvent) {
  if (event.key == "ArrowLeft") {
    dummyImages.value[selectedIdx.value].x--;
    event.preventDefault();
    event.stopPropagation();
  } else if (event.key == "ArrowRight") {
    dummyImages.value[selectedIdx.value].x++;
    event.preventDefault();
    event.stopPropagation();
  }
}

/**
 * Determines the current cursor that should be used in the image viewer.
 */
const cursor = computed(() => {
return dragging.value ? "grabbing" : "grab";
});
</script>

<template>
  <div>Selected Image: {{ selectedIdx + 1 }}</div>
  <div
    ref="glcontainer"
    class="relative size-full"
    :style="{
      cursor: cursor,
    }"
    @click="onClick"
    @contextmenu="onClick"
    @dblclick="resetViewport"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
    @mousemove.stop="onImageMouseMove"
    @mouseup.stop="stopInteractions"
  >
    <canvas ref="glcanvas" />

    <div
      v-for="(img, index) in dummyImages"
      :key="index"
      class="absolute transition-transform duration-75"
      :style="{
        top: img.y + 'px',
        left: img.x + 'px',
        width: img.width + 'px',
        height: img.height + 'px',
        transform: `rotate(${img.rotation}deg)`,
      }"
      :class="['border', index === selectedIdx ? 'border border-yellow-500' : 'border-transparent']"

      
      @mousedown.stop="startDrag(index, $event)"
      @mousedown="onMouseDown($event, index)"
    >
      <img
        :src="arrowImg"
        class="w-full h-full object-contain pointer-events-none"
        alt="Arrow"
      >
  </div>

    <Stitchbar v-model:state="stitchState" @reset-viewport="resetViewport" />
  </div>
</template>
