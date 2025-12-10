<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import { useElementBounding } from "@vueuse/core";
import { snakeCase } from "change-case";
import * as THREE from "three";
import { createStitchEngine, type StitchEngine } from "./stitchGLEngine";
import { appState } from "@/lib/appState";
import { selectedGrayscaleIndex } from "./stitchPoints";
import { getWorkspaceImageUrl } from "./workspace";
import { getTargetSize } from "./api";

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

const grayscaleUrl = computed(() => {
  if (!grayscale.value) return null;
  return getWorkspaceImageUrl(
    grayscale.value.imageLocation,
    appState.workspace!.name
  );
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

  engine.viewport.center.x = size.width / 2;
  engine.viewport.center.y = size.height / 2;
  engine.viewport.zoom = Math.max(
    Math.log(size.width / width.value / fill),
    Math.log(size.height / height.value / fill)
  );
}

// Independent render loop
function startLoop() {
  if (!engine) return;

  function tick() {
    if (!engine) return;

    const vp = engine.viewport;

    const w = width.value * Math.exp(vp.zoom);
    const h = height.value * Math.exp(vp.zoom);

    const x = vp.center.x - w / 2;
    const y = vp.center.y - h / 2;

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
  const scale = Math.exp(engine.viewport.zoom);
  engine.viewport.center.x -= ev.movementX * scale;
  engine.viewport.center.y += ev.movementY * scale;
}

function onWheel(ev: WheelEvent) {
  if (!engine) return;
  engine.viewport.zoom += ev.deltaY / 450;
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
    class="relative w-full h-full bg-black"
    style="cursor: grab"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
  >
    <canvas ref="glcanvas" class="absolute inset-0 w-full h-full" />
  </div>
</template>