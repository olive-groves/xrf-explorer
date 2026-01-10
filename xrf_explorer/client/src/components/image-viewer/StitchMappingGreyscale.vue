<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, reactive } from "vue";
import { useElementBounding } from "@vueuse/core";
import { snakeCase } from "change-case";
import * as THREE from "three";
import { createStitchEngine, type StitchEngine } from "./stitchGLEngine";
import { appState } from "@/lib/appState";
import {
  createGrayPoint,
  selectedGrayscaleIndex,
  setSelectedGrayscaleIndex,
  getRotation,
  checkSelectPoint,
  deselect,
  selectedPointId,
  selectPoint,
  updateGrayPoint,
} from "./stitchPoints";
import { getWorkspaceGreyscaleUrl } from "./workspace";
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
  return getWorkspaceGreyscaleUrl(grayscale.value.imageLocation, appState.workspace!.name);
});

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

// Current origin of the greyscale image
// const grayImageOrigin = reactive({
//   x: 0,
//   y: 0,
// });

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
// The current rotation baked into the layer
const grayRotationRad = ref(0);

/**
 * Function to handle grayscale property changes.
 * @param e - The event containing property change details.
 */
async function onGrayPropChanged(e: Event) {
  const { index, prop } = (e as CustomEvent).detail;

  if (prop === "rotation" && index === selectedGrayscaleIndex.value) {
    await loadGrayscaleLayer(); // recreate layer with new rotation
  }
}

/**
 * Function to load the grayscale image layer into the GL engine.
 */
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

  const id = `gray_${snakeCase(grayscale.value.sourceCubeName)}`;
  currentLayerId = id;

  const rotDeg = getRotation(selectedGrayscaleIndex.value!);
  grayRotationRad.value = (rotDeg * Math.PI) / 180;

  await engine.createImageLayer(id, grayscaleUrl.value, undefined, grayRotationRad.value);
  const layer = engine.layers.find((l) => l.id === currentLayerId);
  if (!layer?.mesh) return;

  // Make sure bounds exist
  layer.mesh.geometry.computeBoundingBox();
  const bb = layer.mesh.geometry.boundingBox!;

  // Center viewport on greyscale geometry
  viewport.center.x = (bb.min.x + bb.max.x) / 2;
  viewport.center.y = (bb.min.y + bb.max.y) / 2;

  // Update the origin
}

/**
 * Function to reset the viewport to fit the grayscale image.
 */
async function resetViewport() {
  if (!engine) return;

  // Find the active greyscale layer
  const layer = engine.layers.find((l) => l.id === currentLayerId);
  if (!layer?.mesh) return;

  const geom = layer.mesh.geometry;

  // Ensure bounds are available
  geom.computeBoundingBox();
  const bb = geom.boundingBox!;

  // Center viewport on visible content
  const contentWidth = bb.max.x - bb.min.x;
  const contentHeight = bb.max.y - bb.min.y;

  viewport.center.x = (bb.min.x + bb.max.x) / 2;
  viewport.center.y = (bb.min.y + bb.max.y) / 2;

  // Fit content into viewport
  const fill = 0.9;

  viewport.zoom = Math.max(Math.log(contentWidth / width.value / fill), Math.log(contentHeight / height.value / fill));
}

/**
 * Function to start the render loop.
 */
function startLoop() {
  if (!engine) return;

  function tick() {
    if (!engine) return;

    // const vp = viewport;

    const w = width.value * Math.exp(viewport.zoom);
    const h = height.value * Math.exp(viewport.zoom);

    const x = viewport.center.x - w / 2;
    const y = viewport.center.y - h / 2;

    viewbox.value = { x, y, w, h };

    // update viewport uniform for all layers
    engine.layers.forEach((layer) => layer.uniform.iViewport.value.set(x, y, w, h));

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

/**
 * Function to handle mouse down event.
 * @param ev - The mouse event.
 */
function onMouseDown(ev: MouseEvent) {
  if (ev.button === 0) dragging.value = true;
}

/**
 * Function to handle mouse up event.
 */
function onMouseUp() {
  dragging.value = false;
}

/**
 * Function to handle mouse leave event.
 */
function onMouseLeave() {
  dragging.value = false;
}

/**
 * Function to handle mouse move event.
 * @param ev - The mouse event.
 */
function onMouseMove(ev: MouseEvent) {
  if (!engine || !dragging.value) return;
  const scale = Math.exp(viewport.zoom);
  viewport.center.x -= ev.movementX * scale;
  viewport.center.y += ev.movementY * scale;
}

/**
 * Function to handle mouse wheel event.
 * @param ev - The wheel event.
 */
function onWheel(ev: WheelEvent) {
  if (!engine) return;
  viewport.zoom += ev.deltaY / 450;
}

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
      for (const p of currentPoints.value) {
        const dx = p.gray.x - pointObj.x;
        const dy = p.gray.y - pointObj.y;
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
        updateGrayPoint(selectedPointId.value, pointObj.x, pointObj.y);
        return;
      }
      createGrayPoint(pointObj.x, pointObj.y);
    }
  }
}

/**
 * Function to get image coordinates from a mouse event.
 * @param event - The mouse event.
 * @returns The coordinates in image space.
 */
function getBaseImageCoords(event: MouseEvent) {
  const rect = glcanvas.value!.getBoundingClientRect();

  const px = event.clientX - rect.left;
  const py = event.clientY - rect.top;

  const zoomScale = Math.exp(viewport.zoom);
  const halfW = width.value / 2;
  const halfH = height.value / 2;

  // screen → world
  const worldX = viewport.center.x + (px - halfW) * zoomScale;
  const worldY = viewport.center.y - (py - halfH) * zoomScale;

  const layer = engine!.layers.find((l) => l.id === currentLayerId);
  if (!layer?.mesh) return { x: 0, y: 0 };

  // world → local image space
  const inv = layer.mesh.matrixWorld.clone().invert();
  const v = new THREE.Vector3(worldX, worldY, 0).applyMatrix4(inv);

  return { x: v.x, y: v.y };
}

// Lifecycle
onMounted(async () => {
  window.addEventListener("stitch:grayscale-prop-changed", onGrayPropChanged as EventListener);
  engine = createStitchEngine(glcanvas.value!);

  await loadGrayscaleLayer();

  startLoop();
});

// Reload layer when selected grayscale changes
watch(grayscaleUrl, async () => {
  await loadGrayscaleLayer();
  await resetViewport();
});

onBeforeUnmount(() => {
  window.removeEventListener("stitch:grayscale-prop-changed", onGrayPropChanged as EventListener);
  engine?.dispose();
  engine = null;
});
</script>

<template>
  <div
    ref="container"
    class="relative size-full"
    style="cursor: crosshair"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
    @click="onClick"
    @contextmenu="onClick"
  >
    <canvas ref="glcanvas" class="absolute inset-0 size-full" />

    <Dots :x="viewbox.x" :y="viewbox.y" :w="viewbox.w" :h="viewbox.h" :zoom="viewport.zoom" :gray-mapping="true" />
  </div>
</template>
