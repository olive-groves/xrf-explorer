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
const points = ref<{ x: number; y: number }[]>([]);
const selectedPoint = ref<number | null>(null);
const maxPoints = 4;

// GL Setup
onMounted(async () => {
  toast.info("Loading stitch viewer, this may take a few minutes...", { duration: 2000 });
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
    const baseId = appState.workspace?.baseImage
      ? `base_${snakeCase(appState.workspace.baseImage.name)}`
      : null;
    if (baseId) {
      const b = layers.value.find((l) => l.id === baseId);
      if (b) disposeLayer(b);
    }
  } catch (e) {
    console.warn("Error disposing layers", e);
  }
  if (animationFrame != null) {
    cancelAnimationFrame(animationFrame);
    animationFrame = null;
  }
});

function createOrUpdateBaseLayer() {
  const ws = appState.workspace;
  if (!ws || !ws.baseImage) return;

  const rawLoc = (ws.baseImage as any).imageLocation ?? "";
  const baseLoc = rawLoc.includes("/") ? rawLoc : ws.baseImage.name;
  const baseUrl = getWorkspaceImageUrl(baseLoc, ws.name);
  const baseId = `base_${snakeCase(ws.baseImage.name || "base")}`;

  let existing = layers.value.find((l) => l.id === baseId);
  if (!existing) {
    const layer = createLayer(baseId, baseUrl);
    layerGroups.value.base = {
      name: ws.baseImage.name,
      description: "Base image (stitch)",
      layers: [layer],
      index: 0,
      visible: true,
      visibility: 1,
      opacity: [1.0],
      contrast: [1.0],
      saturation: [1.0],
      gamma: [1.0],
      brightness: [0.0],
    } as any;
    updateLayerGroupLayers(layerGroups.value.base as any);
  }
}

async function setupGL() {
  try {
    camera = new THREE.OrthographicCamera();
    scene.renderer = new THREE.WebGLRenderer({ alpha: true, canvas: glcanvas.value! });
    scene.renderer.setSize(width.value, height.value);

    createOrUpdateBaseLayer();
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
      const ws = appState.workspace;
      if (ws?.baseImage) {
        const baseId = `base_${snakeCase(ws.baseImage.name || "base")}`;
        const baseLayer = layers.value.find((l) => l.id === baseId);
        if (baseLayer?.mesh) baseLayer.mesh.position.set(0, 0, 0);
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

    animationFrame = requestAnimationFrame(render);
  }

  animationFrame = requestAnimationFrame(render);
}

// Base image
const baseSrc = computed(() => {
  const ws = appState.workspace;
  if (!ws?.baseImage) return null;
  const loc = ws.baseImage.imageLocation?.includes("/") ? ws.baseImage.imageLocation : ws.baseImage.name;
  return getWorkspaceImageUrl(loc, ws.name);
});

watch(baseSrc, (newVal, oldVal) => {
  // Only reset loading state when the base source actually changes.
  if (newVal !== oldVal) baseReady.value = false;
});

// Viewport controls
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

// Selection Points
function getImageCoords(event: MouseEvent) {
  const img = event.target as HTMLImageElement;
  if (!img || !img.naturalWidth) return null;
  const rect = img.getBoundingClientRect();
  const scale = Math.min(rect.width / img.naturalWidth, rect.height / img.naturalHeight);
  const offsetX = (rect.width - img.naturalWidth * scale) / 2;
  const offsetY = (rect.height - img.naturalHeight * scale) / 2;
  return { x: (event.clientX - rect.left - offsetX) / scale, y: (event.clientY - rect.top - offsetY) / scale };
}

function onBaseImageClick(event: MouseEvent) {
  const coords = getImageCoords(event);
  if (!coords) return;

  for (let i = 0; i < points.value.length; i++) {
    const dx = points.value[i].x - coords.x;
    const dy = points.value[i].y - coords.y;
    if (dx * dx + dy * dy < 20 * 20) {
      selectedPoint.value = i;
      return;
    }
  }

  if (selectedPoint.value !== null) {
    points.value[selectedPoint.value] = coords;
    selectedPoint.value = null;
    return;
  }

  if (points.value.length < maxPoints) points.value.push(coords);
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
    :style="{ cursor: cursor }"
    @click="onClick"
    @contextmenu="onClick"
    @dblclick="resetViewport"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
    @mouseup.stop="stopInteractions"
  >
    <!-- WebGL canvas -->
    <canvas ref="glcanvas" class="absolute inset-0 w-full h-full" style="z-index: 0;" />

    <!-- Base image -->
    <div
      v-if="baseSrc"
      class="absolute inset-0 flex items-center justify-center pointer-events-auto"
      :style="{
        zIndex: 1,
        width: '100%',
        height: '100%',
        paddingTop: basePadding + 'px',
        paddingBottom: basePadding + 'px',
        backgroundColor: 'white',
        opacity: baseOpacity
      }"
      @click="onBaseImageClick"
    >
      <img
        :src="baseSrc"
        @load="baseReady = true"
        :style="{
          width: 'auto',
          height: 'auto',
          maxWidth: `calc(100% - ${basePadding * 2}px)`,
          maxHeight: `calc(100% - ${basePadding * 2}px)`,
          display: 'block',
          objectFit: 'contain',
        }"
        class="mx-auto"
      />


      <!-- Points overlay -->
      <div
        v-for="(p, i) in points"
        :key="i"
        class="absolute w-4 h-4 rounded-full border border-black"
        :style="{
          background: i === selectedPoint ? 'blue' : 'red',
          left: p.x + 'px',
          top: p.y + 'px',
          transform: 'translate(-50%, -50%)',
          zIndex: 2
        }"
      ></div>
    </div>

    <!-- Loading overlay -->
    <div
      v-if="!baseReady"
      class="absolute inset-0 flex items-center justify-center bg-black/40 text-white"
      style="z-index: 3"
    >
      <div class="p-4 bg-black/60 rounded">Loading base image...</div>
    </div>
  </div>
</template>