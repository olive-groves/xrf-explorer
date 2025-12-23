<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, reactive } from "vue";
import { useElementBounding } from "@vueuse/core";
import * as THREE from "three";
import { appState } from "@/lib/appState";
import { getWorkspaceImageUrl } from "./workspace";
import { getTargetSize } from "./api";
import { createStitchEngine, type StitchEngine } from "./stitchGLEngine";
import { Layer } from "./types";
import { stitch } from "./stitchHelper";

const glcanvas = ref<HTMLCanvasElement | null>(null);
const container = ref<HTMLDivElement | null>(null);
let baseLayer: Layer | null = null;
let grayLayer: Layer | null = null;

const bounds = useElementBounding(container);
const width = bounds.width;
const height = bounds.height;

let engine: StitchEngine | null = null;
let animationFrame: number | null = null;

// Viewport in image-space coordinates
const viewport = reactive({
  center: { x: 0, y: 0 },
  zoom: 0,
});

let grayLayerId: string | null = null;

function getStitchedGreyscaleUrl() {
  if (!appState.workspace) return null;
  return `/api/${appState.workspace.name}/stitch_datacubes/stitched_greyscale/`;
}

// grayscale offset used for viewport shifting
const grayViewportOffset = { x: 0, y: 0 };



const stitchedGreyscaleUrl = computed(() => {
  return getStitchedGreyscaleUrl();
});

function onBaseOpacityChanged(e: Event) {
  if (!baseLayer) return;
  baseLayer.uniform.uOpacity.value = (e as CustomEvent<number>).detail;
}

function onGrayOpacityChanged(e: Event) {
  if (!grayLayer) return;
  grayLayer.uniform.uOpacity.value = (e as CustomEvent<number>).detail;
}

function onGrayNudge(e: Event) {
  const { dx, dy } = (e as CustomEvent<{ dx: number; dy: number }>).detail;
  applyGrayNudge(dx, dy);
}

// nudging updates viewport offset
function applyGrayNudge(dx: number, dy: number) {
  const scale = Math.exp(viewport.zoom);

  // move by image pixels scaled by zoom
  grayViewportOffset.x += dx * scale;
  grayViewportOffset.y -= dy * scale;
}

function resetGreyscaleOffset() {
  grayViewportOffset.x = 0;
  grayViewportOffset.y = 0;

  // Optional: notify the preview viewer if you want
  window.dispatchEvent(
    new CustomEvent("stitch:gray-nudge", { detail: { dx: 0, dy: 0 } })
  );
}

// GL setup
async function loadGrayscaleLayer() {
  if (!engine) return;

  // Remove previous greyscale layer
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
    grayLayer = null;
  }

  const url = stitchedGreyscaleUrl.value;
  if (!url) return;

  grayLayerId = "stitch_preview_greyscale";
  grayLayer = await engine.createImageLayer(grayLayerId, url);

  grayLayer.uniform.iIndex.value = 0;
  grayViewportOffset.x = 0;
  grayViewportOffset.y = 0;
}

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

    const vp = viewport;
    const zoomScale = Math.exp(vp.zoom);
    const vw = W * zoomScale;
    const vh = H * zoomScale;
    const vx = vp.center.x - vw / 2;
    const vy = vp.center.y - vh / 2;

    engine.layers.forEach((layer) => {
      const v = layer.uniform.iViewport.value;
      if (layer === grayLayer) {
        v.set(
          vx - grayViewportOffset.x,
          vy - grayViewportOffset.y,
          vw,
          vh
        );
      } else {
        v.set(vx, vy, vw, vh);
      }
    });

    // camera & renderer
    engine.renderer.setSize(W, H);
    engine.camera.left = -W / 2;
    engine.camera.right = W / 2;
    engine.camera.top = H / 2;
    engine.camera.bottom = -H / 2;
    engine.camera.updateProjectionMatrix();

    engine.renderer.render(engine.scene, engine.camera);

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
  const scale = Math.exp(viewport.zoom);
  viewport.center.x -= ev.movementX * scale;
  viewport.center.y += ev.movementY * scale;
}
function onWheel(ev: WheelEvent) {
  viewport.zoom += ev.deltaY / 500;
}

function onKeyDown(ev: KeyboardEvent) {
  // Intercept arrow keys globally
  if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(ev.key)) {
    ev.preventDefault();
    ev.stopImmediatePropagation();
    ev.stopPropagation();
  } else {
    return;
  }

  if (!grayLayer) return;

  let dx = 0;
  let dy = 0;

  if (ev.key === "ArrowLeft") dx = -1;
  else if (ev.key === "ArrowRight") dx = 1;
  else if (ev.key === "ArrowUp") dy = -1;
  else if (ev.key === "ArrowDown") dy = 1;

  applyGrayNudge(dx, dy);
}

// lifecycle
onMounted(async () => {
  window.addEventListener("stitch:base-opacity-changed", onBaseOpacityChanged);
  window.addEventListener("stitch:gray-opacity-changed", onGrayOpacityChanged);
  window.addEventListener("stitch:gray-nudge", onGrayNudge);
  window.addEventListener("keydown", onKeyDown, { capture: true });
  window.addEventListener("stitch:reset-offset", resetGreyscaleOffset);
  const ws = appState.workspace;
  if (!ws) return;
  await stitch(true, ws.grayscale[0].sourceCubeType);

  if (!glcanvas.value) return;

  engine = createStitchEngine(glcanvas.value);

  
  if (!ws?.baseImage) return;

  const loc = ws.baseImage.imageLocation?.includes("/")
    ? ws.baseImage.imageLocation
    : ws.baseImage.name;

  baseLayer = await engine.createImageLayer("stitch_base", getWorkspaceImageUrl(loc, ws.name));

  await loadGrayscaleLayer();
  await resetViewport();
  startRenderLoop();
});

watch(stitchedGreyscaleUrl, async () => {
  if (!engine) return;
  await loadGrayscaleLayer();
  await resetViewport();
});

onBeforeUnmount(() => {
  window.removeEventListener("stitch:base-opacity-changed", onBaseOpacityChanged);
  window.removeEventListener("stitch:gray-opacity-changed", onGrayOpacityChanged);
  window.removeEventListener("stitch:gray-nudge", onGrayNudge);
  window.removeEventListener("keydown", onKeyDown);
  window.removeEventListener("stitch:reset-offset", resetGreyscaleOffset);

  if (animationFrame != null) cancelAnimationFrame(animationFrame);
  if (engine) engine.dispose();
});
</script>

<template>
  <div
    ref="container"
    class="relative w-full h-full"
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