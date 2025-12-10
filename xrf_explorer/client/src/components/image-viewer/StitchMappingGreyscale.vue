<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, reactive } from "vue";
import { useElementBounding } from "@vueuse/core";
import { snakeCase } from "change-case";
import * as THREE from "three";
import { createStitchEngine, type StitchEngine } from "./stitchGLEngine";
import { appState } from "@/lib/appState";
import { createGrayPoint, grayscalePoints, selectedGrayscaleIndex, setSelectedGrayscaleIndex } from "./stitchPoints";
import { getWorkspaceImageUrl } from "./workspace";
import { getTargetSize } from "./api";
import Dots from "./Dots.vue";

// GL engine instance
let engine: StitchEngine | null = null;

const glcanvas = ref<HTMLCanvasElement | null>(null);
const container = ref<HTMLDivElement | null>(null);

// Track container size reactively
const bounds = useElementBounding(container);
const width = bounds.width;
const height = bounds.height;

// Resolve selected grayscale
const grayscale = computed(() => {
  const idx = selectedGrayscaleIndex.value;
  if (idx == null) return null;
  return appState.workspace?.grayscale?.[idx] ?? null;
});

window.addEventListener("stitch:selected-grayscale", (e: Event) => {
  const i = (e as CustomEvent).detail as number;
  setSelectedGrayscaleIndex(i);
});

const grayscaleUrl = computed(() => {
  if (!grayscale.value) return null;
  return getWorkspaceImageUrl(
    grayscale.value.imageLocation,
    appState.workspace!.name
  );
});

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

// Track the GL layer currently displayed
let currentLayerId: string | null = null;

// Layer loading
async function loadGrayscaleLayer() {
  if (!engine) return;

  // Remove old layer
  if (currentLayerId) {
    const idx = engine.layers.findIndex((l) => l.id === currentLayerId);
    if (idx >= 0) {
      const layer = engine.layers[idx];
      if (layer.mesh) {
        layer.mesh.geometry.dispose();
        (layer.mesh.material as THREE.Material).dispose();
        engine.scene.remove(layer.mesh);
      }
      engine.layers.splice(idx, 1);
    }
    currentLayerId = null;
  }

  if (!grayscale.value || !grayscaleUrl.value) return;

  const id = `gray_${snakeCase(grayscale.value.name)}`;
  currentLayerId = id;

  await engine.createImageLayer(id, grayscaleUrl.value);
}

// Viewport reset
async function resetViewport() {
  if (!engine) return;
  const size = await getTargetSize();
  const fill = 0.9;

  viewport.center.x = size.width / 2;
  viewport.center.y = size.height / 2;
  viewport.zoom = Math.max(
    Math.log(size.width / width.value / fill),
    Math.log(size.height / height.value / fill)
  );
}

// Independent render loop
function startLoop() {
  if (!engine) return;

  function tick() {
    if (!engine) return;

    // const vp = viewport;

    const w = width.value * Math.exp(viewport.zoom);
    const h = height.value * Math.exp(viewport.zoom);

    const x = viewport.center.x - w / 2;
    const y = viewport.center.y - h / 2;
    viewbox.value = { x: x, y: y, w: w, h: h };

    // update viewport uniform for all layers
    engine.layers.forEach((layer) =>
      layer.uniform.iViewport.value.set(x, y, w, h)
    );

    // Resize renderer
    engine.renderer.setSize(width.value, height.value);

    // Update camera
    engine.camera.left = -width.value / 2;
    engine.camera.right = width.value / 2;
    engine.camera.top = height.value / 2;
    engine.camera.bottom = -height.value / 2;
    engine.camera.updateProjectionMatrix();

    engine.renderer.render(engine.scene, engine.camera);

    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

// Mouse controls
const dragging = ref(false);

function onMouseDown(ev: MouseEvent) {
  if (ev.button === 0) dragging.value = true;
}
function onMouseUp() {
  dragging.value = false;
}
function onMouseLeave() {
  dragging.value = false;
}

function onMouseMove(ev: MouseEvent) {
  if (!engine || !dragging.value) return;
  const scale = Math.exp(viewport.zoom);
  viewport.center.x -= ev.movementX * scale;
  viewport.center.y += ev.movementY * scale;
}

function onWheel(ev: WheelEvent) {
  if (!engine) return;
  viewport.zoom += ev.deltaY / 450;
}

function onClick(event: MouseEvent) {
  if (event.button == 2) {
    // Prevent opening of context menu.
    event.preventDefault();

    if (appState.stitching) {
      const pointObj = getBaseImageCoords(event);
      createGrayPoint(pointObj.x, pointObj.y)
  
    }
  }
}

function getBaseImageCoords(event: MouseEvent) {
  const rect = glcanvas.value!.getBoundingClientRect();

  const px = event.clientX - rect.left;
  const py = event.clientY - rect.top;

  const zoomScale = Math.exp(viewport.zoom);

  const halfW = width.value / 2;
  const halfH = height.value / 2;

  // Convert screen pixel → world space
  const worldX = viewport.center.x + (px - halfW) * zoomScale;
  const worldY = viewport.center.y - (py - halfH) * zoomScale;
  
  // Base image = world coordinates
  return { x: worldX, y: worldY };
}


// Lifecycle
onMounted(async () => {
  engine = createStitchEngine(glcanvas.value!);

  await loadGrayscaleLayer();
  await resetViewport();
  startLoop();
});

// Reload layer when selected grayscale changes
watch(grayscaleUrl, async () => {
  await loadGrayscaleLayer();
  await resetViewport();
});

onBeforeUnmount(() => {
  engine?.dispose();
  engine = null;
});
</script>

<template>
  <div
    ref="container"
    class="relative w-full h-full"
    style="cursor: crosshair"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
    @click="onClick"
    @contextmenu="onClick"
  >
    <canvas ref="glcanvas" class="absolute inset-0 w-full h-full" />

    <Dots
      :x="viewbox.x"
      :y="viewbox.y"
      :w="viewbox.w"
      :h="viewbox.h"
      :zoom="viewport.zoom"
      />
  </div>
</template>