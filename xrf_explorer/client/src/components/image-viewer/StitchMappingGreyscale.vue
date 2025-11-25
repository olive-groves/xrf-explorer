<script setup lang="ts">
import { ref, computed, inject, onMounted, onBeforeUnmount, watch } from "vue";
import { StitchTool, StitchState } from "./types";
import { FrontendConfig } from "@/lib/config";
import { toast } from "vue-sonner";
import { SelectionAreaType } from "@/lib/selection";
import { scene, disposeLayer } from "./scene";
import { createLayer, layerGroups, updateLayerGroupLayers, layers } from "./state";
import * as THREE from "three";
import { snakeCase } from "change-case";
import { useElementBounding } from "@vueuse/core";
import { appState } from "@/lib/appState";
import { getWorkspaceImageUrl } from "./workspace";
import { getTargetSize } from "./api";
import type { CSSProperties } from "vue";

const config = inject<FrontendConfig>("config")!;

const glcontainer = ref<HTMLDivElement | null>(null);
const glcanvas = ref<HTMLCanvasElement | null>(null);

let camera: THREE.OrthographicCamera | null = null;
let animationFrame: number | null = null;

const viewport = {
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

let zoomLimitReached = false;

const baseReady = ref(false);
const baseOpacity = ref(1.0);
const basePadding = 20;

const dragging = ref(false);
const draggingIndex = ref<number | null>(null);

// Points selection
import {
  grayscalePoints,
  selectedPointId,
  selectedGrayscaleIndex,
  createGrayPoint,
  updateGrayPoint,
  selectPoint,
  checkSelectPoint,
  deselect,
  setSelectedGrayscaleIndex
} from "./stitchPoints";

// points for the currently selected grayscale
const currentPoints = computed(() => {
  const idx = selectedGrayscaleIndex.value ?? null;
  if (idx === null) return [];
  if (!grayscalePoints.value[idx]) grayscalePoints.value[idx] = [];
  return grayscalePoints.value[idx];
});

const pointRefresh = ref(0);

// Use shared selectedGrayscaleIndex
const selectedGrayscale = computed(() => {
  const idx = selectedGrayscaleIndex.value ?? null;
  if (idx === null) return null;
  return appState.workspace?.grayscale?.[idx] ?? null;
});

// update the shared selected index
window.addEventListener("stitch:selected-grayscale", (e: Event) => {
  const i = (e as CustomEvent).detail as number;
  setSelectedGrayscaleIndex(i);
});

// GL Setup 
onMounted(async () => {
  toast.info("Loading stitch viewer, this may take a few minutes...", { duration: 1000 });
  await setupGL();
});

onBeforeUnmount(() => {
  // Dispose GL layers
  try {
    const g = appState.workspace?.grayscale ?? [];
    g.forEach((entry: any) => {
      const id = `stitch_gray_${snakeCase(entry.name)}`;
      const layer = layers.value.find((l) => l.id === id);
      if (layer) disposeLayer(layer);
    });
  } catch (e) {
    console.warn("Error disposing layers", e);
  }
  if (animationFrame != null) {
    cancelAnimationFrame(animationFrame);
    animationFrame = null;
  }
});

function createOrUpdateGrayscaleLayer() {
  const gs = selectedGrayscale.value;
  if (!gs) return;

  const url = getWorkspaceImageUrl(gs.imageLocation, appState.workspace!.name);
  const id = `stitch_gray_${snakeCase(gs.name)}`;
  let existing = layers.value.find((l) => l.id === id);
  if (!existing) {
    const layer = createLayer(id, url);
    layerGroups.value.selectedGray = {
      name: gs.name,
      description: "Selected grayscale",
      layers: [layer],
      index: 0,
      visible: true,
      opacity: [1.0],
      contrast: [1.0],
      saturation: [1.0],
      gamma: [1.0],
      brightness: [0.0],
    } as any;
    updateLayerGroupLayers(layerGroups.value.selectedGray as any);
  }
}

async function setupGL() {
  try {
    camera = new THREE.OrthographicCamera();
    scene.renderer = new THREE.WebGLRenderer({ alpha: true, canvas: glcanvas.value! });
    scene.renderer.setSize(width.value, height.value);

    createOrUpdateGrayscaleLayer();
    try {
      await resetViewport();
    } catch (e) {
      console.warn("resetViewport failed", e);
    }

    startRenderLoop();
  } catch (e) {
    console.warn("Failed to initialize GL", e);
  }
}

function startRenderLoop() {
  if (!scene.renderer) return;

  function render() {
    const w = width.value * Math.exp(viewport.zoom);
    const h = height.value * Math.exp(viewport.zoom);
    const x = viewport.center.x - w / 2;
    const y = viewport.center.y - h / 2;

    layers.value.forEach((layer) => {
      if (layer.uniform?.iViewport) layer.uniform.iViewport.value.set(x, y, w, h);

      if (layer.uniform?.uRadius) {
        const lensSize = stitchState.value.lensSize?.[0] ?? 0;
        layer.uniform.uRadius.value = selectionToolActive.value ? Math.max(0, lensSize) : Number.MAX_VALUE;
      }
    });

    scene.renderer!.setSize(width.value, height.value);

    try {
      const gs = selectedGrayscale.value;
      if (gs) {
        const id = `stitch_gray_${snakeCase(gs.name)}`;
        const layer = layers.value.find((l) => l.id === id);
        if (layer?.mesh) layer.mesh.position.set(0, 0, 0);
      }
    } catch (e) {}

    if (camera) {
      const halfW = width.value / 2;
      const halfH = height.value / 2;
      camera.left = -halfW;
      camera.right = halfW;
      camera.top = halfH;
      camera.bottom = -halfH;
      camera.updateProjectionMatrix();
      scene.renderer!.render(scene.scene, camera);
    }
    pointRefresh.value++; 
    animationFrame = requestAnimationFrame(render);
  }

  animationFrame = requestAnimationFrame(render);
}

// Selected Grayscale Image
const greyScaleSrc = computed(() => {
  const gs = selectedGrayscale.value;
  if (!gs) return null;
  return getWorkspaceImageUrl(gs.imageLocation, appState.workspace!.name);
});

watch(greyScaleSrc, (newVal, oldVal) => {
  // Only reset loading state when the grayscale source actually changes.
  if (newVal !== oldVal) baseReady.value = false;
});

// Viewport Controls
function resetViewport() {
  return getTargetSize().then((size) => {
    const fill = 0.9;
    viewport.center.x = size.width / 2;
    viewport.center.y = size.height / 2;
    viewport.zoom = Math.max(
      Math.log(size.width / width.value / fill),
      Math.log(size.height / height.value / fill),
    );
  });
}

function onClick(event: MouseEvent) {
  if (event.button === 2) event.preventDefault();
}

function onMouseUp(event: MouseEvent) {
  if (event.button === 0 || (event.button === 2 && selectionToolActive.value)) dragging.value = false;
}

function onMouseLeave() {
  dragging.value = false;
}

function onMouseMove(event: MouseEvent) {
  if (dragging.value) {
    const scale = Math.exp(viewport.zoom) * stitchState.value.movementSpeed[0];
    viewport.center.x -= event.movementX * scale;
    viewport.center.y += event.movementY * scale;
  }
}

function onWheel(event: WheelEvent) {
  viewport.zoom += (event.deltaY / 500) * stitchState.value.scrollSpeed[0];
  if (viewport.zoom >= config.imageViewer.zoomLimit || viewport.zoom <= -config.imageViewer.zoomLimit) {
    viewport.zoom = Math.min(config.imageViewer.zoomLimit, Math.max(-config.imageViewer.zoomLimit, viewport.zoom));
    if (!zoomLimitReached) {
      toast.info("Zoom limit reached");
      zoomLimitReached = true;
    }
  } else zoomLimitReached = false;
}

// Points
function onBaseImageClick(event: MouseEvent) {
  const img = glcontainer.value?.querySelector("img");
  if (!img) return;

  const { x, y } = computeToImageCoords(event, img);

  // Clicking near an existing point selects it
  for (const p of currentPoints.value) {
    const dx = p.gray.x - x;
    const dy = p.gray.y - y;
    if (dx * dx + dy * dy < 20 * 20) {
      if (checkSelectPoint(p.id)) {
        deselect();
        return;
      }
      selectPoint(p.id);
      return;
    }
  }

  // Move selected point
  if (selectedPointId.value !== null) {
    updateGrayPoint(selectedPointId.value, x, y);
    return;
  }

  // Create new point
  createGrayPoint(x, y);
}
function toDisplayCoords(p: { x: number; y: number }, i: number): CSSProperties {
  pointRefresh.value;

  const img = glcontainer.value?.querySelector("img");
  if (!img || !img.naturalWidth || !img.naturalHeight) return {};

  const rect = img.getBoundingClientRect();
  const scale = Math.min(rect.width / img.naturalWidth, rect.height / img.naturalHeight);

  const offsetX = (rect.width - img.naturalWidth * scale) / 2;
  const offsetY = (rect.height - img.naturalHeight * scale) / 2;

  const screenX = rect.left + offsetX + p.x * scale;
  const screenY = rect.top + offsetY + p.y * scale;

  return {
    position: "fixed",
    left: `${screenX}px`,
    top: `${screenY}px`,
    width: "10px",
    height: "10px",
    borderRadius: "50%",
    backgroundColor: i === selectedPointId.value ? "blue" : "red",
    transform: "translate(-50%, -50%)",
    pointerEvents: "none",
    zIndex: 9999,
  };
}

function computeToImageCoords(event: MouseEvent, img: HTMLImageElement) {
  const rect = img.getBoundingClientRect();
  const scale = Math.min(rect.width / img.naturalWidth, rect.height / img.naturalHeight);
  const offsetX = (rect.width - img.naturalWidth * scale) / 2;
  const offsetY = (rect.height - img.naturalHeight * scale) / 2;

  const x = (event.clientX - rect.left - offsetX) / scale;
  const y = (event.clientY - rect.top - offsetY) / scale;

  return { x, y };
}

function labelCoords(p: { x: number; y: number }, i: number): CSSProperties {
  const coords = toDisplayCoords(p, i);
  return {
    position: "fixed",
    left: coords.left,
    top: coords.top,
    transform: "translate(-50%, -120%)",
    color: "white",
    textShadow: "0 0 4px black, 0 0 6px black",
    pointerEvents: "none",
    zIndex: 10000,
  };
}

function stopInteractions() {
  draggingIndex.value = null;
}

const cursor = computed(() => (dragging.value ? "grabbing" : "grab"));
</script>

<template>
  <div
    ref="glcontainer"
    class="relative w-full h-full"
    :style="{ cursor: cursor, backgroundColor: 'black' }"
    @click="onClick"
    @contextmenu="onClick"
    @dblclick="resetViewport"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
    @mouseup.stop="stopInteractions"
  >
    <canvas ref="glcanvas" class="absolute inset-0 w-full h-full" style="z-index: 0;" />

    <!-- Selected Grayscale Image -->
    <div
      v-if="greyScaleSrc"
      class="absolute inset-0 flex items-center justify-center pointer-events-auto
            bg-white dark:bg-black"
      :style="{ 
        zIndex: 1, 
        paddingTop: basePadding + 'px', 
        paddingBottom: basePadding + 'px', 
        opacity: baseOpacity 
      }"
      @click="onBaseImageClick"
    >
      <img
        :src="greyScaleSrc"
        class="w-full h-full object-contain"
        :style="{ maxHeight: `calc(100% - ${basePadding * 2}px)` }"
        @load="baseReady = true"
      />

      <!-- Points overlay -->
      <div v-for="(p, i) in currentPoints" :key="p.id">
        <!-- Point Dot -->
        <div
          class="absolute w-4 h-4 rounded-full border border-black dark:border-white"
          :style="toDisplayCoords(p.gray, p.id)"
        ></div>

        <!-- Label -->
        <div
          class="absolute text-xs font-bold text-black dark:text-white"
          :style="labelCoords(p.gray, p.id)"
        >
          {{ i + 1 }}
        </div>
      </div>
    </div>

    <!-- Loading overlay -->
    <div
      v-if="!baseReady"
      class="absolute inset-0 flex items-center justify-center bg-black/40 dark:bg-black text-white"
      style="z-index: 3"
    >
      <div class="p-4 bg-black/60 dark:bg-black rounded">Loading grayscale image...</div>
    </div>
</div>
</template>