<script setup lang="ts">
import { ref, computed, inject, onMounted, onBeforeUnmount, reactive } from "vue";
import { FrontendConfig } from "@/lib/config";
import { useElementBounding } from "@vueuse/core";
import { appState } from "@/lib/appState";
import { getWorkspaceImageUrl } from "./workspace";
import { getTargetSize } from "./api";
import { createStitchEngine, StitchEngine } from "./stitchGLEngine";
import { StitchTool, StitchState } from "./types";
import { SelectionAreaType } from "@/lib/selection";
import { toast } from "vue-sonner";
import Dots from "./Dots.vue";
import {
  checkSelectPoint,
  deselect,
  selectedGrayscaleIndex,
  selectedPointId,
  selectPoint,
  updateBasePoint,
  hasBase,
} from "./stitchPoints";

const config = inject<FrontendConfig>("config")!;

const glcontainer = ref<HTMLDivElement | null>(null);
const glcanvas = ref<HTMLCanvasElement | null>(null);

const canvasSize = useElementBounding(glcontainer);
const width = canvasSize.width;
const height = canvasSize.height;

const stitchState = ref<StitchState>({
  tool: StitchTool.Grab,
  movementSpeed: [config.imageViewer.defaultMovementSpeed],
  scrollSpeed: [config.imageViewer.defaultScrollSpeed],
  lensSize: [config.imageViewer.defaultLensSize],
});

const selectionToolActive = computed(() =>
  Object.values(SelectionAreaType as { [key: string]: string }).includes(stitchState.value.tool as string),
);

const viewbox = ref<{
  x: number;
  y: number;
  w: number;
  h: number;
}>({
  x: 0,
  y: 0,
  w: 0,
  h: 0,
});

// Viewport in image-space coordinates
const viewport = reactive<{
  center: { x: number; y: number };
  zoom: number;
}>({
  center: { x: 0, y: 0 },
  zoom: 0,
});

const dragging = ref(false);
const lensLocked = ref(false);
let engine: StitchEngine | null = null;
let animationFrame: number | null = null;

let zoomLimitReached = false;

// Wether the layer is loaded
const isLoading = ref(true);

onMounted(async () => {
  if (!glcanvas.value) return;

  try {
    isLoading.value = true;

    engine = createStitchEngine(glcanvas.value);

    const ws = appState.workspace;
    if (!ws?.baseImage) return;

    const loc = ws.baseImage.imageLocation?.includes("/")
      ? ws.baseImage.imageLocation
      : ws.baseImage.name;

    const url = getWorkspaceImageUrl(loc, ws.name);

    await engine.createImageLayer("stitch_base", url);
    await resetViewport();
    startRenderLoop();
  } catch (err) {
    console.error(err);
    toast.error("Failed to load image");
  } finally {
    isLoading.value = false;
  }
});

onBeforeUnmount(() => {
  if (animationFrame != null) {
    cancelAnimationFrame(animationFrame);
    animationFrame = null;
  }
  engine?.dispose();
  engine = null;
});

/**
 * Function to reset the viewport to fit the image.
 */
async function resetViewport() {
  if (!engine) return;
  const size = await getTargetSize();
  const fill = 0.9;
  viewport.center.x = size.width / 2;
  viewport.center.y = size.height / 2;
  viewport.zoom = Math.max(Math.log(size.width / width.value / fill), Math.log(size.height / height.value / fill));
}

/**
 * Function to start the render loop.
 */
function startRenderLoop() {
  if (!engine) return;

  const render = () => {
    if (!engine) return;

    const w = width.value * Math.exp(viewport.zoom);
    const h = height.value * Math.exp(viewport.zoom);
    const x = viewport.center.x - w / 2;
    const y = viewport.center.y - h / 2;
    viewbox.value = { x: x, y: y, w: w, h: h };
    engine.layers.forEach(
      (layer: {
        uniform: {
          iViewport: { value: { set: (arg0: number, arg1: number, arg2: number, arg3: number) => void } };
          uRadius: { value: number };
        };
      }) => {
        layer.uniform.iViewport.value.set(x, y, w, h);

        if (layer.uniform.uRadius) {
          const lensSize = stitchState.value.lensSize?.[0] ?? 0;
          layer.uniform.uRadius.value = selectionToolActive.value ? Math.max(0, lensSize) : Number.MAX_VALUE;
        }
      },
    );

    const halfW = width.value / 2;
    const halfH = height.value / 2;

    engine.camera.left = -halfW;
    engine.camera.right = halfW;
    engine.camera.top = halfH;
    engine.camera.bottom = -halfH;
    engine.camera.updateProjectionMatrix();

    engine.renderer.setSize(width.value, height.value);
    engine.renderer.render(engine.scene, engine.camera);

    animationFrame = requestAnimationFrame(render);
  };

  animationFrame = requestAnimationFrame(render);
}
/**
 * Function to handle mouse down event.
 * @param event - The mouse event.
 */
function onMouseDown(event: MouseEvent) {
  if (!engine) return;

  if (event.button == 2) {
    lensLocked.value = !lensLocked.value;
    onMouseMove(event);
  }

  if (event.button == 0 && !selectionToolActive.value) {
    dragging.value = true;
  }
}

/**
 * Function to handle mouse up event.
 * @param event - The mouse event.
 */
function onMouseUp(event: MouseEvent) {
  if (event.button == 0) {
    dragging.value = false;
  }
}

/**
 * Function to handle mouse leave event.
 */
function onMouseLeave() {
  dragging.value = false;
}

/**
 * Function to handle mouse move event.
 * @param event - The mouse event.
 */
function onMouseMove(event: MouseEvent) {
  if (!engine) return;

  if (dragging.value) {
    const scale = Math.exp(viewport.zoom) * stitchState.value.movementSpeed[0];
    viewport.center.x -= event.movementX * scale;
    viewport.center.y += event.movementY * scale;
  }

  const rect = glcanvas.value!.getBoundingClientRect();
  const mouseX = event.clientX - canvasSize.left.value;
  const mouseY = event.clientY - canvasSize.top.value;

  const normalizedX = (width.value * mouseX) / rect.width;
  const normalizedY = height.value * (1 - mouseY / rect.height);

  if (!lensLocked.value) {
    engine.layers.forEach(
      (layer: { uniform: { uMouse: { value: { set: (arg0: number, arg1: number) => void } } } }) => {
        layer.uniform.uMouse.value.set(normalizedX, normalizedY);
      },
    );
  }
}

/**
 * Function to handle mouse wheel event.
 * @param event - The wheel event.
 */
function onWheel(event: WheelEvent) {
  if (!engine) return;

  viewport.zoom += (event.deltaY / 500.0) * stitchState.value.scrollSpeed[0];

  if (viewport.zoom >= config.imageViewer.zoomLimit || viewport.zoom <= -config.imageViewer.zoomLimit) {
    viewport.zoom = Math.min(config.imageViewer.zoomLimit, Math.max(-config.imageViewer.zoomLimit, viewport.zoom));
    if (!zoomLimitReached) {
      toast.info("Zoom limit reached");
      zoomLimitReached = true;
    }
  } else {
    zoomLimitReached = false;
  }
}

/**
 * Function to get image coordinates from a mouse event.
 * @param event - The mouse event.
 * @returns The coordinates in image space.
 */
function getBaseImageCoords(event: MouseEvent) {
  if (!engine || !glcanvas.value) return { x: 0, y: 0 };

  const rect = glcanvas.value.getBoundingClientRect();

  const px = event.clientX - rect.left;
  const py = event.clientY - rect.top;

  const zoomScale = Math.exp(viewport.zoom);

  const halfW = width.value / 2;
  const halfH = height.value / 2;

  const worldX = viewport.center.x + (px - halfW) * zoomScale;
  const worldY = viewport.center.y - (py - halfH) * zoomScale;

  return { x: worldX, y: worldY };
}
// hmm
const currentPoints = computed(() => {
  const ws = appState.workspace;
  if (!ws) return [];
  const idx = selectedGrayscaleIndex.value;
  if (idx === null || idx === undefined) return [];

  if (!ws.mapping.grayscalePoints[idx]) {
    ws.mapping.grayscalePoints[idx] = [];
  }
  return ws.mapping.grayscalePoints[idx];
});

/**
 * Function to handle mouse click event.
 * @param event - The mouse event.
 */
function onClick(event: MouseEvent) {
  if (event.button == 2) {
    // Prevent opening of context menu.
    event.preventDefault();

    if (appState.workspace?.stitchingMode) {
      const pointObj = getBaseImageCoords(event);
      for (const p of currentPoints.value.filter(hasBase)) {
        const dx = p.base.x - pointObj.x;
        const dy = p.base.y - pointObj.y;
        if (dx * dx + dy * dy < 20 * 20) {
          if (checkSelectPoint(p.id)) {
            deselect();
            return;
          }
          selectPoint(p.id);
          return;
        }
      }
      if (selectedPointId.value !== null) {
        updateBasePoint(selectedPointId.value, pointObj.x, pointObj.y);
        return;
      }
    }
  }
}
</script>

<template>
  <div
    ref="glcontainer"
    class="relative size-full"
    style="cursor: crosshair"
    @click="onClick"
    @contextmenu="onClick"
    @dblclick="resetViewport"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
  >
    <div
      v-if="isLoading"
      class="absolute inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
    >
      <div class="rounded-lg bg-background px-6 py-4 shadow-lg flex items-center gap-3">
        <span class="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full" />
        <span class="text-sm font-medium">Loading image…</span>
      </div>
    </div>
    <canvas ref="glcanvas" class="absolute inset-0 size-full" />
    <Dots :x="viewbox.x" :y="viewbox.y" :w="viewbox.w" :h="viewbox.h" :zoom="viewport.zoom" :gray-mapping="false" />
  </div>
</template>
