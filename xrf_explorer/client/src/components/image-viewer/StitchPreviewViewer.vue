<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, reactive } from "vue";
import { useElementBounding } from "@vueuse/core";
import * as THREE from "three";
import { appState } from "@/lib/appState";
import { getWorkspaceImageUrl } from "./workspace";
import { getTargetSize } from "./api";
import { createStitchEngine, type StitchEngine } from "./stitchGLEngine";
import { Layer } from "./types";
import { stitchAndWait } from "./stitchHelper";

// Make sure we do not cache old preview layers
THREE.Cache.enabled = false;

// Viewer
const glcanvas = ref<HTMLCanvasElement | null>(null);
const container = ref<HTMLDivElement | null>(null);
let baseLayer: Layer | null = null;
let grayLayer: Layer | null = null;

// Viewer size
const bounds = useElementBounding(container);
const width = bounds.width;
const height = bounds.height;

// The scaling factor for generating the preview
const grayOptimalScale = ref(1);

// Version of the loaded preview
// Increases when we load the preview to avoid cache issues
const previewVersion = ref(0);

// Render engine
let engine: StitchEngine | null = null;
let animationFrame: number | null = null;

// Viewport in image-space coordinates
const viewport = reactive({
  center: { x: 0, y: 0 },
  zoom: 0,
});

// The size we need to map the preview image to
const stitchedSize = reactive({
  width: 0,
  height: 0,
});

let baseMesh = null;
let baseWidth = 0;
let baseHeight = 0;


/**
 * Function to change the scaling factor
 * @param e - The event that communicates that the scaling factor has beed changed
 */
function onGrayOptimalScale(e: Event) {
  const { factor } = (e as CustomEvent<{ factor: number }>).detail;
  grayOptimalScale.value = factor || 1;
}

// The greyscale URL
const stitchedGreyscaleUrl = computed(() => {
  return getStitchedGreyscaleUrl();
});

/**
 * Function to retrieve the stitched greyscale URL
 */
function getStitchedGreyscaleUrl() {
  if (!appState.workspace) return null;
  return `/api/${appState.workspace.name}/stitch_datacubes/stitched_greyscale/?v=${previewVersion.value}`;
}

// grayscale offset used for viewport shifting
const grayViewportOffset = { x: 0, y: 0 };

/**
 * Function to change the base image opacity
 * @param e - The event that communicates that the opacity needs to be changed
 */
function onBaseOpacityChanged(e: Event) {
  if (!baseLayer) return;
  baseLayer.uniform.uOpacity.value = (e as CustomEvent<number>).detail;
}


/**
 * Function to change the greyscale opacity
 * @param e - The event that communicates that the opacity needs to be changed
 */
function onGrayOpacityChanged(e: Event) {
  if (!grayLayer) return;
  grayLayer.uniform.uOpacity.value = (e as CustomEvent<number>).detail;
}

/**
 * Fucntion to move the stitched greyscale
 * @param e - The event that tells that the greyscale needs to be moved
 */
function onGrayNudge(e: Event) {
  const { dx, dy } = (e as CustomEvent<{ dx: number; dy: number }>).detail;
  applyGrayNudge(dx, dy);
}

/**
 * Update the viewport offset
 * @param dx - The amount we shift on the x-xxis
 * @param dy - The amount we shift in the y-axis
 */
function applyGrayNudge(dx: number, dy: number) {
  const scale = Math.exp(viewport.zoom);

  // move by image pixels scaled by zoom
  grayViewportOffset.x += dx * scale;
  grayViewportOffset.y -= dy * scale;
}

/**
 * Update the viewport to reset the greyscale offset 
 */
function resetGreyscaleOffset() {
  grayViewportOffset.x = 0;
  grayViewportOffset.y = 0;
}

/**
 * Function to get contrast values from the workspace
 */
function getGreyscaleIntensities(): number[] {
  const ws = appState.workspace;
  if (!ws) return [];

  return ws.grayscale.map((_, idx) => {
    return ws.mapping.grayscaleContrast?.[idx] ?? 1.0;
  });
}

// Wether image layers are busy being loaded
const isLoading = ref(false);
const hasRenderedOnce = ref(false);

// Keep track of the most recently loaded image
let loadToken = 0;

/**
 * Function to create and load the preview greyscale layer
 */
async function loadGrayscaleLayer() {
  if (!engine) return;

  const token = ++loadToken;
  isLoading.value = true;
  hasRenderedOnce.value = false;

  let newLayer: Layer | null = null;

  try {
    const url = stitchedGreyscaleUrl.value;
    if (!url) return;

    const newId = `stitch_preview_greyscale_${token}`;

    newLayer = await engine.createImageLayer(
      newId,
      url,
      { width: baseWidth, height: baseHeight }
    );

    if (token !== loadToken) return;

    // wait for texture upload
    const tex = (newLayer.mesh!.material as THREE.RawShaderMaterial)
      .uniforms.tImage.value as THREE.Texture;

    if (!tex.image) {
      await new Promise<void>((resolve) => {
        tex.onUpdate = () => resolve();
      });
    }

    // wait one rendered frame
    await new Promise(requestAnimationFrame);

    // Swap layers
    const oldLayer = grayLayer;

    grayLayer = newLayer;
    grayLayer.uniform.iIndex.value = 0;
    grayViewportOffset.x = 0;
    grayViewportOffset.y = 0;

    // remove old layer
    if (oldLayer) {
      const idx = engine.layers.indexOf(oldLayer);
      if (idx >= 0) engine.layers.splice(idx, 1);

      const mesh = oldLayer.mesh!;
      mesh.geometry.dispose();

      const mat = mesh.material as THREE.RawShaderMaterial;
      const texOld = (mat.uniforms as any).tImage?.value as THREE.Texture | undefined;
      if (texOld) texOld.dispose();

      mat.dispose();
      engine.scene.remove(mesh);
    }

  } catch (err) {
    console.error("Failed to load grayscale preview", err);

    // clean up failed layer
    if (newLayer?.mesh) {
      engine.scene.remove(newLayer.mesh);
      newLayer.mesh.geometry.dispose();
      (newLayer.mesh.material as THREE.Material).dispose();
    }
  }
}

/**
 * Function to reset the viewport
 */
async function resetViewport() {
  if (!engine) return;
  const size = await getTargetSize();
  const targetSize = size;

  stitchedSize.width = targetSize.width;
  stitchedSize.height = targetSize.height;

  const fill = 0.9;

  viewport.center.x = targetSize.width / 2;
  viewport.center.y = targetSize.height / 2;
  viewport.zoom = Math.max(
    Math.log(targetSize.width / width.value / fill),
    Math.log(targetSize.height / height.value / fill)
  );
}

/**
 * Function for rendering the viewer
 */
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

    if (grayLayer && !hasRenderedOnce.value) {
      hasRenderedOnce.value = true;
      isLoading.value = false;
    }

    animationFrame = requestAnimationFrame(render);
  };

  animationFrame = requestAnimationFrame(render);
}

// mouse interaction
const dragging = ref(false);

/**
 * Function for handling mouse clicks
 * @param ev - The mouse event
 */
function onMouseDown(ev: MouseEvent) {
  if (ev.button === 0) dragging.value = true;
}

/**
 * Function for handling mouse releases
 * @param ev - The mouse event
 */
function onMouseUp() {
  dragging.value = false;
}

/**
 * Function for handling the mouse leaving a component
 */
function onMouseLeave() {
  dragging.value = false;
}

/**
 * Function for handling mouse movement
 * @param ev - The mouse event
 */
function onMouseMove(ev: MouseEvent) {
  if (!engine || !dragging.value) return;
  const scale = Math.exp(viewport.zoom);
  viewport.center.x -= ev.movementX * scale;
  viewport.center.y += ev.movementY * scale;
}

/**
 * Function for handling scroling the mouse wheel
 * @param ev - The scroll event
 */
function onWheel(ev: WheelEvent) {
  viewport.zoom += ev.deltaY / 500;
}

/**
 * Function for handling ket presses
 * @param ev - The keyboard event
 */
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

// lifecycle, creates engine and creates base image
onMounted(async () => {
  isLoading.value = true;
  window.addEventListener("stitch:base-opacity-changed", onBaseOpacityChanged);
  window.addEventListener("stitch:gray-opacity-changed", onGrayOpacityChanged);
  window.addEventListener("stitch:gray-nudge", onGrayNudge);
  window.addEventListener("keydown", onKeyDown, { capture: true });
  window.addEventListener("stitch:reset-offset", resetGreyscaleOffset);
  window.addEventListener("stitch:gray-optimal-scale", onGrayOptimalScale);
  const ws = appState.workspace;
  if (!ws) return;
  const intensities = getGreyscaleIntensities();
  await stitchAndWait(true, ws.grayscale[0].sourceCubeType, 1, intensities);
  previewVersion.value++;
  if (!glcanvas.value) return;

  engine = createStitchEngine(glcanvas.value);

  
  if (!ws?.baseImage) return;

  const loc = ws.baseImage.imageLocation?.includes("/")
    ? ws.baseImage.imageLocation
    : ws.baseImage.name;

  baseLayer = await engine.createImageLayer("stitch_base", getWorkspaceImageUrl(loc, ws.name));

  baseMesh = baseLayer.mesh!;
  baseMesh.geometry.computeBoundingBox();
  baseWidth = baseMesh.geometry.boundingBox!.max.x;
  baseHeight = baseMesh.geometry.boundingBox!.max.y;

  await loadGrayscaleLayer();
  await resetViewport();
  startRenderLoop();
});

// Reload stitched greyscale when contrast changes
watch(
  () => appState.workspace?.mapping.grayscaleContrast,
  async () => {
    const ws = appState.workspace;
    if (!ws) return;
    const intensities = getGreyscaleIntensities();
    try {
      await stitchAndWait(
        true,
        ws.grayscale[0].sourceCubeType,
        grayOptimalScale.value,
        intensities
      );
      previewVersion.value++;
      await loadGrayscaleLayer();
    } catch (e) {
      console.warn("Failed to update stitch preview with contrast", e);
    }
  },
  { deep: true }
);

// Reload greyscale layer when greyscale changes
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
  window.removeEventListener("stitch:gray-optimal-scale", onGrayOptimalScale);
  if (animationFrame != null) cancelAnimationFrame(animationFrame);
  if (engine) engine.dispose();
});
</script>

<template>
  <div
    ref="container"
    class="relative w-full h-full"
    :class="{ 'pointer-events-none': isLoading }"
    :style="{ cursor: dragging ? 'grabbing' : 'grab' }"
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
      <span class="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      <span class="text-sm font-medium">Updating preview…</span>
    </div>
  </div>
    <canvas ref="glcanvas" class="absolute inset-0 w-full h-full" />
  </div>
</template>