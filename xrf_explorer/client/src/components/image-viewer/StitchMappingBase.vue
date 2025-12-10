<script setup lang="ts">
import { ref, computed, inject, onMounted, onBeforeUnmount } from "vue";
import { FrontendConfig } from "@/lib/config";
import { useElementBounding } from "@vueuse/core";
import { appState } from "@/lib/appState";
import { getWorkspaceImageUrl } from "./workspace";
import { getTargetSize } from "./api";
import { createStitchEngine, StitchEngine } from "./stitchGLEngine";
import { StitchTool, StitchState } from "./types";
import { SelectionAreaType } from "@/lib/selection";
import { toast } from "vue-sonner";

// stitchPoints
import {
  selectedPointId,
  selectedGrayscaleIndex,
  updateBasePoint,
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
  Object.values(SelectionAreaType as { [key: string]: string }).includes(
    stitchState.value.tool as string,
  ),
);

const dragging = ref(false);
const lensLocked = ref(false);
let engine: StitchEngine | null = null;
let animationFrame: number | null = null;

let zoomLimitReached = false;

onMounted(async () => {
  if (!glcanvas.value) return;

  engine = createStitchEngine(glcanvas.value);

  // Create base image layer inside this local engine
  const ws = appState.workspace;
  if (!ws?.baseImage) return;

  const loc = ws.baseImage.imageLocation?.includes("/")
    ? ws.baseImage.imageLocation
    : ws.baseImage.name;
  const url = getWorkspaceImageUrl(loc, ws.name);

  await engine.createImageLayer("stitch_base", url);

  await resetViewport();
  startRenderLoop();
});

onBeforeUnmount(() => {
  if (animationFrame != null) {
    cancelAnimationFrame(animationFrame);
    animationFrame = null;
  }
  engine?.dispose();
  engine = null;
});

async function resetViewport() {
  if (!engine) return;
  const size = await getTargetSize();
  const fill = 0.9;
  engine.viewport.center.x = size.width / 2;
  engine.viewport.center.y = size.height / 2;
  engine.viewport.zoom = Math.max(
    Math.log((size.width / width.value) / fill),
    Math.log((size.height / height.value) / fill),
  );
}

function startRenderLoop() {
  if (!engine) return;

  const render = () => {
    if (!engine) return;

    const w = width.value * Math.exp(engine.viewport.zoom);
    const h = height.value * Math.exp(engine.viewport.zoom);
    const x = engine.viewport.center.x - w / 2;
    const y = engine.viewport.center.y - h / 2;

    engine.layers.forEach((layer: { uniform: { iViewport: { value: { set: (arg0: number, arg1: number, arg2: number, arg3: number) => void; }; }; uRadius: { value: number; }; }; }) => {
      layer.uniform.iViewport.value.set(x, y, w, h);

      if (layer.uniform.uRadius) {
        const lensSize = stitchState.value.lensSize?.[0] ?? 0;
        layer.uniform.uRadius.value = selectionToolActive.value
          ? Math.max(0, lensSize)
          : Number.MAX_VALUE;
      }
    });

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

function onMouseUp(event: MouseEvent) {
  if (event.button == 0) {
    dragging.value = false;
  }
}

function onMouseLeave() {
  dragging.value = false;
}

function onMouseMove(event: MouseEvent) {
  if (!engine) return;

  if (dragging.value) {
    const scale = Math.exp(engine.viewport.zoom) * stitchState.value.movementSpeed[0];
    engine.viewport.center.x -= event.movementX * scale;
    engine.viewport.center.y += event.movementY * scale;
  }

  const rect = glcanvas.value!.getBoundingClientRect();
  const mouseX = event.clientX - canvasSize.left.value;
  const mouseY = event.clientY - canvasSize.top.value;

  const normalizedX = (width.value * mouseX) / rect.width;
  const normalizedY = height.value * (1 - mouseY / rect.height);

  if (!lensLocked.value) {
    engine.layers.forEach((layer: { uniform: { uMouse: { value: { set: (arg0: number, arg1: number) => void; }; }; }; }) => {
      layer.uniform.uMouse.value.set(normalizedX, normalizedY);
    });
  }
}

function onWheel(event: WheelEvent) {
  if (!engine) return;

  engine.viewport.zoom +=
    (event.deltaY / 500.0) * stitchState.value.scrollSpeed[0];

  if (
    engine.viewport.zoom >= config.imageViewer.zoomLimit ||
    engine.viewport.zoom <= -config.imageViewer.zoomLimit
  ) {
    engine.viewport.zoom = Math.min(
      config.imageViewer.zoomLimit,
      Math.max(-config.imageViewer.zoomLimit, engine.viewport.zoom),
    );
    if (!zoomLimitReached) {
      toast.info("Zoom limit reached");
      zoomLimitReached = true;
    }
  } else {
    zoomLimitReached = false;
  }
}

function getBaseImageCoords(event: MouseEvent) {
  if (!engine || !glcanvas.value) return { x: 0, y: 0 };

  const rect = glcanvas.value.getBoundingClientRect();

  const px = event.clientX - rect.left;
  const py = event.clientY - rect.top;

  const zoomScale = Math.exp(engine.viewport.zoom);

  const halfW = width.value / 2;
  const halfH = height.value / 2;

  const worldX = engine.viewport.center.x + (px - halfW) * zoomScale;
  const worldY = engine.viewport.center.y - (py - halfH) * zoomScale;

  return { x: worldX, y: worldY };
}

function onClick(event: MouseEvent) {
  if (event.button === 2) {
    event.preventDefault();
    return;
  }

  if (event.button !== 0) return;
  if (selectedGrayscaleIndex.value == null) return;
  if (selectedPointId.value == null) return;

  const pos = getBaseImageCoords(event);
  updateBasePoint(selectedPointId.value, pos.x, pos.y);
}

const cursor = computed(() => (dragging.value ? "grabbing" : "grab"));
</script>

<template>
  <div
    ref="glcontainer"
    class="relative w-full h-full"
    :style="{ cursor }"
    @click="onClick"
    @contextmenu.prevent
    @dblclick="resetViewport"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
  >
    <canvas ref="glcanvas" class="absolute inset-0 w-full h-full" />
  </div>
</template>