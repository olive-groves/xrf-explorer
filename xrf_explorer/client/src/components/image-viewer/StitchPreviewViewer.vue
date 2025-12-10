<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import { useElementBounding } from "@vueuse/core";
import * as THREE from "three";
import { snakeCase } from "change-case";

import { appState } from "@/lib/appState";
import { getWorkspaceImageUrl } from "./workspace";
import { getTargetSize } from "./api";
import { createStitchEngine, type StitchEngine } from "./stitchGLEngine";

const glcanvas = ref<HTMLCanvasElement | null>(null);
const container = ref<HTMLDivElement | null>(null);

const bounds = useElementBounding(container);
const width = bounds.width;
const height = bounds.height;

let engine: StitchEngine | null = null;
let animationFrame: number | null = null;

// current grayscale layer id in this engine
let grayLayerId: string | null = null;

const tempGreysclaleInx = 0;

// greyscale url
const selectedGrayscale = computed(() => {
  const idx = tempGreysclaleInx;
  if (idx == null) return null;
  return appState.workspace?.grayscale?.[idx] ?? null;
});

const grayscaleUrl = computed(() => {
  const gs = selectedGrayscale.value;
  if (!gs) return null;
  return getWorkspaceImageUrl(gs.imageLocation, appState.workspace!.name);
});

// small reactive tick so overlays recompute when viewport moves
const overlayTick = ref(0);

// GL setup
async function loadGrayscaleLayer() {
  if (!engine) return;

  // remove old layer if any
  if (grayLayerId) {
    const idx = engine.layers.findIndex((l) => l.id === grayLayerId);
    if (idx >= 0) {
      const layer = engine.layers[idx];
      if (layer.mesh) {
        layer.mesh.geometry.dispose();
        (layer.mesh.material as THREE.Material).dispose();
        engine.scene.remove(layer.mesh);
      }
      engine.layers.splice(idx, 1);
    }
    grayLayerId = null;
  }

  if (!selectedGrayscale.value || !grayscaleUrl.value) return;

  const id = `stitch_gray_${snakeCase(selectedGrayscale.value.name)}`;
  grayLayerId = id;

  const layer = await engine.createImageLayer(id, grayscaleUrl.value);

  layer.uniform.iIndex.value = 0;
  if (layer.mesh) {
    layer.mesh.renderOrder = 0;
  }
}

async function resetViewport() {
  if (!engine) return;
  const size = await getTargetSize();
  const fill = 0.9;

  engine.viewport.center.x = size.width / 2;
  engine.viewport.center.y = size.height / 2;
  engine.viewport.zoom = Math.max(
    Math.log(size.width / width.value / fill),
    Math.log(size.height / height.value / fill),
  );
}

function startRenderLoop() {
  if (!engine) return;

  const render = () => {
    if (!engine) return;

    const W = width.value;
    const H = height.value;
    if (W <= 0 || H <= 0) {
      animationFrame = requestAnimationFrame(render);
      return;
    }

    const vp = engine.viewport;
    const zoomScale = Math.exp(vp.zoom);
    const vw = W * zoomScale;
    const vh = H * zoomScale;
    const vx = vp.center.x - vw / 2;
    const vy = vp.center.y - vh / 2;

    // update viewport uniform on all layer
    engine.layers.forEach((layer) => {
      layer.uniform.iViewport.value.set(vx, vy, vw, vh);
    });

    // camera & renderer
    engine.renderer.setSize(W, H);
    engine.camera.left = -W / 2;
    engine.camera.right = W / 2;
    engine.camera.top = H / 2;
    engine.camera.bottom = -H / 2;
    engine.camera.updateProjectionMatrix();

    engine.renderer.render(engine.scene, engine.camera);

    // bump overlay tick so overlay positions recompute
    overlayTick.value++;

    animationFrame = requestAnimationFrame(render);
  };

  animationFrame = requestAnimationFrame(render);
}

// mouse interaction
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
  const vp = engine.viewport;
  const scale = Math.exp(vp.zoom);
  vp.center.x -= ev.movementX * scale;
  vp.center.y += ev.movementY * scale;
}

function onWheel(ev: WheelEvent) {
  if (!engine) return;
  engine.viewport.zoom += ev.deltaY / 500;
}

// lifecycle
onMounted(async () => {
  if (!glcanvas.value) return;

  engine = createStitchEngine(glcanvas.value);

  // Make sure camera actually sees the plane
  engine.camera.position.set(0, 0, 10);
  engine.camera.lookAt(0, 0, 0);

  await loadGrayscaleLayer();
  await resetViewport();
  startRenderLoop();
});

watch(grayscaleUrl, async () => {
  if (!engine) return;
  await loadGrayscaleLayer();
  await resetViewport();
});

onBeforeUnmount(() => {
  if (animationFrame != null) {
    cancelAnimationFrame(animationFrame);
    animationFrame = null;
  }
  if (engine) {
    engine.dispose();
    engine = null;
  }
});
</script>

<template>
  <div
    ref="container"
    class="relative w-full h-full bg-black"
    :style="{ cursor: dragging ? 'grabbing' : 'grab' }"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
  >
    <canvas ref="glcanvas" class="absolute inset-0 w-full h-full" />
  </div>
</template>