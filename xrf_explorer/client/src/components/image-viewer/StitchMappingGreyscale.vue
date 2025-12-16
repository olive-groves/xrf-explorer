<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, reactive } from "vue";
import { useElementBounding } from "@vueuse/core";
import { snakeCase } from "change-case";
import * as THREE from "three";
import { createStitchEngine, type StitchEngine } from "./stitchGLEngine";
import { appState } from "@/lib/appState";
import { createGrayPoint, selectedGrayscaleIndex, setSelectedGrayscaleIndex, getRotation, grayscalePoints, checkSelectPoint, deselect, selectedPointId, selectPoint, updateGrayPoint } from "./stitchPoints";
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

// hmm
const currentPoints = computed(() => {
  const idx = selectedGrayscaleIndex.value ?? null;
  if (idx === null) return [];
  if (!grayscalePoints.value[idx]) grayscalePoints.value[idx] = [];
  return grayscalePoints.value[idx];
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

  const rot = getRotation(selectedGrayscaleIndex.value!);
  applyGrayRotation(rot);
}

function onGrayPropChanged(e: Event) {
  const { index, prop, value } = (e as CustomEvent).detail;
  if (prop === "rotation" && index === selectedGrayscaleIndex.value) {
    applyGrayRotation(value);
  }
}

function applyGrayRotation(deg: number) {
  if (!engine) return;
  const layer = engine.layers.find(l => l.id === currentLayerId);
  if (!layer) return;

  const tex = layer.uniform.tImage?.value as THREE.Texture;
  const img = tex?.image as HTMLImageElement;
  if (!img) return;

  const W = img.width;
  const H = img.height;

  // world-space pivot (because geometry is scaled)
  const cx = W / 2;
  const cy = H / 2;

  const rad = (deg * Math.PI) / 180;
  const c = Math.cos(rad);
  const s = Math.sin(rad);

  const m = layer.uniform.mRegister.value as THREE.Matrix3;

  // Build world-space rotation around image center
  m.set(
     c, -s,  cx - c*cx + s*cy,
     s,  c,  cy - s*cx - c*cy,
     0,  0,  1
  );
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

    let w = width.value * Math.exp(viewport.zoom);
    let h = height.value * Math.exp(viewport.zoom);

    const rot = getRotation(selectedGrayscaleIndex.value ?? 0);
    if (rot !== 0) {
      const a = (rot * Math.PI) / 180;
      const absCos = Math.abs(Math.cos(a));
      const absSin = Math.abs(Math.sin(a));

      // rotated bounding box of the viewport rectangle
      const newW = w * absCos + h * absSin;
      const newH = w * absSin + h * absCos;

      w = newW;
      h = newH;
    }

    const x = viewport.center.x - w / 2;
    const y = viewport.center.y - h / 2;

    viewbox.value = { x, y, w, h };

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
  window.addEventListener(
  "stitch:grayscale-prop-changed",
  onGrayPropChanged as EventListener
  );
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
  window.removeEventListener(
  "stitch:grayscale-prop-changed",
  onGrayPropChanged as EventListener
  );
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
      :grayMapping="true"
      />
  </div>
</template>