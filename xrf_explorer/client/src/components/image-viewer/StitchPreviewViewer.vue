<script setup lang="ts">
import Stitchbar from "@/components/image-viewer/Stitchbar.vue";
import { computed, inject, onBeforeUnmount, ref, onMounted, watch } from "vue";
import { StitchTool, StitchState } from "./types";
import { useElementBounding } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { toast } from "vue-sonner";
import { SelectionAreaType } from "@/lib/selection";

import { scene, disposeLayer } from "./scene";
import { createLayer, layerGroups, updateLayerGroupLayers, layers } from "./state";
import * as THREE from "three";
import { snakeCase } from "change-case";

const config = inject<FrontendConfig>("config")!;

const glcontainer = ref<HTMLDivElement | null>(null);
const glcanvas = ref<HTMLCanvasElement | null>(null);

let camera: THREE.OrthographicCamera | null = null;
let animationFrame: number | null = null;

const viewport: {
  center: { x: number; y: number };
  zoom: number;
} = {
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

// Flag to prevent the zoom limit toast from being shown multiple times
let zoomLimitReached = false;

// Image boxes
interface ImageBox {
  name: string;
  src: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  opacity?: number;
}

const greyscaleImages = ref<ImageBox[]>([]);
const selectedIdx = ref(0);
const showDomBase = ref(true);
const baseReady = ref(false);

// opacity for the base image (controlled by StitchWindow slider)
const baseOpacity = ref(1.0);

// Vertical padding (px) to leave above and below the base DOM fallback image.
const basePadding = 20;

const draggingIndex = ref<number | null>(null);
const dragOffset = ref({ x: 0, y: 0 });

onMounted(() => {
  window.addEventListener("keydown", onKeyDown);
  // listen for base opacity changes from the StitchWindow slider
  window.addEventListener('stitch:base-opacity-changed', onBaseOpacityChanged as EventListener);
  // listen for grayscale opacity changes targeted at the selected grayscale
  window.addEventListener('stitch:selected-grayscale-opacity-changed', onSelectedGrayscaleOpacityChanged as EventListener);
  // listen for per-index grayscale prop changes (opacity/rotation/xOffset/yOffset)
  window.addEventListener('stitch:grayscale-prop-changed', onGrayscalePropChanged as EventListener);
  // Ensure we have latest workspace so grayscale entries are visible
  ensureWorkspaceHasGrayscale().then(async () => {
    toast.info("Loading preview, this may take a few minutes...", { duration: 2000 });
    await setupGL();
    await loadGrayscaleImages();
  });
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeyDown);
  window.removeEventListener('stitch:base-opacity-changed', onBaseOpacityChanged as EventListener);
  window.removeEventListener('stitch:selected-grayscale-opacity-changed', onSelectedGrayscaleOpacityChanged as EventListener);
  window.removeEventListener('stitch:grayscale-prop-changed', onGrayscalePropChanged as EventListener);
  // dispose any GL layers we created for this viewer
  try {
    const g = appState.workspace?.grayscale ?? [];
    g.forEach((entry: any) => {
      const id = `stitch_gray_${snakeCase(entry.name)}`;
      const layer = layers.value.find((l) => l.id === id);
      if (layer) disposeLayer(layer);
    });
    // dispose base layer
    const baseId = appState.workspace && appState.workspace.baseImage ? `base_${snakeCase(appState.workspace.baseImage.name)}` : null;
    if (baseId) {
      const b = layers.value.find((l) => l.id === baseId);
      if (b) disposeLayer(b);
    }
  } catch (e) {
    console.warn("Error disposing stitchviewer layers", e);
  }
  // stop render loop
  if (animationFrame != null) {
    cancelAnimationFrame(animationFrame);
    animationFrame = null;
  }
});

function startDrag(index: number, e: MouseEvent) {
  // Only allow dragging when using Grab tool
  if (stitchState.value.tool !== StitchTool.Grab) return;
  draggingIndex.value = index;
  const img = greyscaleImages.value[index];
  const rect = glcontainer.value?.getBoundingClientRect();
  if (!rect) return;

  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  dragOffset.value = {
    x: mouseX - img.x,
    y: mouseY - img.y
  };
}

/** Handle base opacity changes dispatched by StitchWindow */
function onBaseOpacityChanged(e: Event | CustomEvent) {
  try {
    const detail = (e as CustomEvent).detail;
    const v = Number(Array.isArray(detail) ? detail[0] : detail ?? detail);
    if (isNaN(v)) return;
    const clamped = Math.max(0, Math.min(1, v));
    baseOpacity.value = clamped;

    // Update GL base layer/group if present
    try {
      if (layerGroups.value.base) {
        layerGroups.value.base.opacity[0] = clamped;
        updateLayerGroupLayers(layerGroups.value.base as any);
      }
      // Also update direct layer uniform if present
      const ws = appState.workspace;
      if (ws && ws.baseImage) {
        const baseId = `base_${snakeCase(ws.baseImage.name || "base")}`;
        const baseLayer = layers.value.find((l) => l.id === baseId);
        if (baseLayer && baseLayer.uniform && baseLayer.uniform.uOpacity) {
          baseLayer.uniform.uOpacity.value = clamped;
        }
      }
    } catch (err) {
      console.warn('Could not update GL base opacity', err);
    }
  } catch (err) {
    console.warn('Error handling base opacity event', err);
  }
}

/** Handle opacity changes for the currently selected grayscale (from StitchWindow) */
function onSelectedGrayscaleOpacityChanged(e: Event | CustomEvent) {
  try {
    const detail = (e as CustomEvent).detail;
    const v = Number(Array.isArray(detail) ? detail[0] : detail ?? detail);
    if (isNaN(v)) return;
    const clamped = Math.max(0, Math.min(1, v));
    // update the selected image box if exists
    const idx = selectedIdx.value;
    if (idx != null && greyscaleImages.value[idx]) {
      greyscaleImages.value[idx].opacity = clamped;
      // also update GL layer uniform if present
      const img = greyscaleImages.value[idx];
      const id = `stitch_gray_${img.name}`;
      const layer = layers.value.find((l) => l.id === id);
      if (layer && layer.uniform && layer.uniform.uOpacity) {
        layer.uniform.uOpacity.value = clamped;
      }
    }
  } catch (err) {
    console.warn('Error handling selected grayscale opacity change', err);
  }
}

function applyGrayscaleProp(index: number, prop: string, value: number) {
  const idx = Number(index);
  if (isNaN(idx) || idx < 0 || idx >= greyscaleImages.value.length) return;
  const img = greyscaleImages.value[idx];
  if (!img) return;

  if (prop === 'opacity') {
    img.opacity = Number(value);
    const id = `stitch_gray_${img.name}`;
    const layer = layers.value.find((l) => l.id === id);
    if (layer && layer.uniform && (layer.uniform as any).uOpacity) {
      (layer.uniform as any).uOpacity.value = Number(value);
    }
  } else if (prop === 'rotation') {
    img.rotation = Number(value);
    const id = `stitch_gray_${img.name}`;
    const layer = layers.value.find((l) => l.id === id);
    if (layer && layer.mesh) {
      layer.mesh.rotation.set(0, 0, (Number(value) * Math.PI) / 180);
    }
  } else if (prop === 'xOffset') {
    img.x = Number(value);
    const id = `stitch_gray_${img.name}`;
    const layer = layers.value.find((l) => l.id === id);
    if (layer && layer.mesh) {
      layer.mesh.position.set(img.x + img.width / 2, img.y + img.height / 2, 0);
    }
  } else if (prop === 'yOffset') {
    img.y = Number(value);
    const id = `stitch_gray_${img.name}`;
    const layer = layers.value.find((l) => l.id === id);
    if (layer && layer.mesh) {
      layer.mesh.position.set(img.x + img.width / 2, img.y + img.height / 2, 0);
    }
  }
}

function onGrayscalePropChanged(e: Event | CustomEvent) {
  try {
    const detail = (e as CustomEvent).detail;
    if (!detail) return;
    const { index, prop, value } = detail as { index: number; prop: string; value: number };
    applyGrayscaleProp(index, prop, value);
  } catch (err) {
    console.warn('Error handling grayscale prop change', err);
  }
}

// announce selection changes to other components so they can update a slider
watch(selectedIdx, (idx) => {
  try {
    const img = greyscaleImages.value[idx];
    const name = img ? img.name : null;
    const opacity = img ? (img.opacity ?? 1) : 1;
    window.dispatchEvent(new CustomEvent('stitch:selected-grayscale-changed', { detail: { name, opacity } }));
  } catch (e) {
    console.warn('Could not dispatch selected grayscale changed', e);
  }
});

// Helpers to load grayscale images from workspace
import { appState } from "@/lib/appState";
import { getImageSize } from "./api";
import { getWorkspaceImageUrl } from "./workspace";
import { getTargetSize } from "./api";

async function ensureWorkspaceHasGrayscale() {
  try {
    const ws = appState.workspace;
    if (!ws) return;
    if (ws.grayscale && ws.grayscale.length > 0) return;

    const resp = await fetch(`${config.api.endpoint}/${ws.name}/workspace`);
    if (!resp.ok) return;
    const updated = await resp.json();
    appState.workspace = updated;
  } catch (e) {
    console.warn("Could not refresh workspace for grayscale images", e);
  }
}

async function loadGrayscaleImages() {
  greyscaleImages.value = [];
  const ws = appState.workspace;
  if (!ws || !ws.grayscale || ws.grayscale.length === 0) return;

  // place images in a grid initial layout
  const padding = 20;
  const cols = Math.max(1, Math.floor(width.value / 250));

  for (let i = 0; i < ws.grayscale.length; i++) {
    const g = ws.grayscale[i];
  const src = getWorkspaceImageUrl(g.imageLocation, ws.name);
    let size = null;
    try {
      size = await getImageSize(g.imageLocation);
    } catch (e) {
      size = null;
    }
    let w = 200;
    let h = 200;
    if (size) {
      // scale down to max dimension while preserving aspect ratio
      const maxDim = 300; // maximum displayed size per image
      const scale = Math.min(1, maxDim / Math.max(size.width, size.height));
      w = Math.round(size.width * scale);
      h = Math.round(size.height * scale);
    }

    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = padding + col * (200 + padding);
    const y = padding + row * (200 + padding);

    greyscaleImages.value.push({
      name: g.name || `grayscale_${i}`,
      src,
      x,
      y,
        width: w,
        height: h,
        rotation: 0,
        opacity: 1,
    });
  }

  // Also create GL layers for the grayscales
  try {
    // create base layer if not present
    // ensure base layer exists and wait until it's loaded into GL
    createOrUpdateBaseLayer();
    // wait for base GL mesh to be available before creating grayscale GL layers
    const baseId = appState.workspace && appState.workspace.baseImage ? `base_${snakeCase(appState.workspace.baseImage.name)}` : null;
    if (baseId) {
      const ok = await waitForLayerMesh(baseId, 30000);
      // mark baseReady true when the GL mesh becomes ready. 
      if (ok) {
        baseReady.value = true;
      } else {
        console.warn("Base GL layer did not become ready within timeout");
      }
    }

    // create grayscale GL layers only after base is ready
    if (baseReady.value) {
      for (let i = 0; i < ws.grayscale.length; i++) {
        const g = ws.grayscale[i];
        const id = `stitch_gray_${snakeCase(g.name)}`;
        const url = getWorkspaceImageUrl(g.imageLocation, ws.name);
        // create layer
        const existing = layers.value.find((l) => l.id === id);
        if (!existing) {
          const l = createLayer(id, url);
          // attach to a stitch group
          if (!layerGroups.value.stitch) {
            layerGroups.value.stitch = {
              name: "Stitch",
              description: "Stitch viewer generated images",
              layers: [l],
              index: -2,
              visible: true,
              visibility: 1,
              opacity: [1],
              contrast: [1],
              saturation: [1],
              gamma: [1],
              brightness: [0],
            } as any;
          } else {
            layerGroups.value.stitch.layers.push(l);
          }
        }
      }

      if (layerGroups.value.stitch) updateLayerGroupLayers(layerGroups.value.stitch as any);
    }
  } catch (e) {
    console.warn("Could not create GL grayscale layers", e);
  }
}

/** Poll until layer.mesh exists (texture/mesh loaded into GL) or timeout */
function waitForLayerMesh(layerId: string, timeoutMs: number = 30000): Promise<boolean> {
  return new Promise((resolve) => {
    const start = Date.now();
    const iv = setInterval(() => {
      const layer = layers.value.find((l) => l.id === layerId);
      if (layer && layer.mesh) {
        clearInterval(iv);
        resolve(true);
        return;
      }
      if (Date.now() - start > timeoutMs) {
        clearInterval(iv);
        resolve(false);
      }
    }, 200);
  });
}

/** Ensure the GL base layer exists and is attached to a layer group */
function createOrUpdateBaseLayer() {
  const ws = appState.workspace;
  if (!ws || !ws.baseImage) return;
  // If the configured imageLocation is a path-like location (contains '/'), use it directly
  // otherwise use the base image NAME so the server will resolve the actual file via workspace.json
  const rawLoc = (ws.baseImage as any).imageLocation ?? "";
  const baseLoc = rawLoc && rawLoc.includes("/") ? rawLoc : ws.baseImage.name;
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
      ...{
        visibility: 1,
        opacity: [1.0],
        contrast: [1.0],
        saturation: [1.0],
        gamma: [1.0],
        brightness: [0.0],
      },
    } as any;
    updateLayerGroupLayers(layerGroups.value.base as any);
  }
}

async function checkDomBaseAvailable() {
  const src = baseSrc.value;
  if (!src) {
    showDomBase.value = false;
    return;
  }
  try {
    const resp = await fetch(src, { method: "HEAD" });
    showDomBase.value = resp.ok;
    if (!resp.ok) console.warn("Base DOM image HEAD returned", resp.status, resp.statusText, src);
  } catch (e) {
    console.warn("Base DOM image fetch failed", e, src);
    showDomBase.value = false;
  }
}

function onDomBaseLoad() {
  // DOM base image loaded successfully — clear the loading overlay so users
  // can interact while GL textures finish loading in the background.
  showDomBase.value = true;
  baseReady.value = true;
}

function onDomBaseError(e: Event) {
  console.warn('Base image failed to load (DOM)', e, baseSrc.value);
  showDomBase.value = false;
}

/** Simple GL setup for stitch viewer */
async function setupGL() {
  // create camera and renderer using the canvas in this component
  try {
    camera = new THREE.OrthographicCamera();
    scene.renderer = new THREE.WebGLRenderer({ alpha: true, canvas: glcanvas.value! });
    // ensure renderer size matches container
    scene.renderer.setSize(width.value, height.value);
    // initialize base layer if workspace present
    createOrUpdateBaseLayer();
    // initialize viewport to show the target image
    try {
      await resetViewport();
    } catch (e) {
      console.warn("resetViewport failed in StitchViewer", e);
    }
    // start render loop for this view
    startRenderLoop();
  } catch (e) {
    console.warn("Failed to initialize GL for stitchviewer", e);
  }
}

function startRenderLoop() {
  if (!scene.renderer) return;

  function render() {
    // Calculate viewport parameters
    const w = width.value * Math.exp(viewport.zoom);
    const h = height.value * Math.exp(viewport.zoom);
    const x = viewport.center.x - w / 2;
    const y = viewport.center.y - h / 2;

    // Update uniforms for all layers so shaders know viewport
    layers.value.forEach((layer) => {
      if (layer.uniform && layer.uniform.iViewport) {
        layer.uniform.iViewport.value.set(x, y, w, h);
      }
      // lens radius and mouse handled similarly if available
        if (layer.uniform && layer.uniform.uRadius) {
          // Use the stitch toolbar lens size when an appropriate tool is active.
          // If the current tool isn't a selection/lens tool, set the radius to a very large
          // value to effectively disable the lens in the shader.
          try {
            const lensSize = stitchState.value.lensSize?.[0] ?? 0;
            // Determine if a selection/lens tool is active — reuse existing computed
            const selectionActive = Object.values(SelectionAreaType as { [key: string]: string }).includes(stitchState.value.tool as string);
            layer.uniform.uRadius.value = selectionActive ? Math.max(0, lensSize) : Number.MAX_VALUE;
          } catch (e) {
            // Fallback: disable lens
            layer.uniform.uRadius.value = Number.MAX_VALUE;
          }
        }
    });

    // ensure renderer size matches container
    scene.renderer!.setSize(width.value, height.value);

    // Sync DOM tile positions to GL meshes
    try {
      for (let i = 0; i < greyscaleImages.value.length; i++) {
        const img = greyscaleImages.value[i];
        const id = `stitch_gray_${img.name}`;
        const layer = layers.value.find((l) => l.id === id);
        if (layer && layer.mesh) {
          // Position mesh so its center aligns with DOM top-left coordinate system.
          // Mesh geometry is created with origin at (0,0) lower-left in ImageViewer, so we shift to center.
          const centerX = img.x + img.width / 2;
          const centerY = img.y + img.height / 2;
          // Convert to GL coordinate system where (0,0) is bottom-left: we keep consistent with viewport
          layer.mesh.position.set(centerX, centerY, 0);
          layer.mesh.rotation.set(0, 0, (img.rotation * Math.PI) / 180.0);
          // If width/height differ from original, scale mesh
          // ensure bounding box is calculated
          try {
            if ((layer.mesh.geometry as any).computeBoundingBox) (layer.mesh.geometry as any).computeBoundingBox();
          } catch (e) {}

          const bb = (layer.mesh.geometry as any).boundingBox;
          const bw = bb ? (bb.max.x - bb.min.x) : 1;
          const bh = bb ? (bb.max.y - bb.min.y) : 1;
          const sx = img.width / bw;
          const sy = img.height / bh;
          if (!isNaN(sx) && !isNaN(sy) && isFinite(sx) && isFinite(sy)) {
            layer.mesh.scale.set(sx, sy, 1);
          }
        }
      }
      // also sync base image if present
      const ws = appState.workspace;
      if (ws && ws.baseImage) {
        const baseId = `base_${snakeCase(ws.baseImage.name || "base")}`;
        const baseLayer = layers.value.find((l) => l.id === baseId);
        if (baseLayer && baseLayer.mesh) {
          // base should be at (0,0)
          baseLayer.mesh.position.set(0, 0, 0);
          baseLayer.mesh.rotation.set(0, 0, 0);
        }
      }
    } catch (e) {
      // ignore per-frame sync errors
    }

    // Update camera to match canvas and render
    if (camera) {
      // Orthographic camera parameters: left, right, top, bottom
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

  // start
  animationFrame = requestAnimationFrame(render);
}

// Compute base image URL to show as background
const baseSrc = computed(() => {
  const ws = appState.workspace;
  if (!ws || !ws.baseImage) return null;
  // If the configured imageLocation is a path-like location, use it directly
  // otherwise use the base image NAME so the server will resolve the actual file via workspace.json
  const rawLoc = (ws.baseImage as any).imageLocation ?? "";
  const loc = rawLoc && rawLoc.includes("/") ? rawLoc : ws.baseImage.name;
  return getWorkspaceImageUrl(loc, ws.name);
});

watch(baseSrc, () => checkDomBaseAvailable());


// When toolbar state changes (lens size / tool), update existing layer uniforms immediately
watch(
  () => [stitchState.value.lensSize?.[0], stitchState.value.tool],
  () => {
    const selectionActive = Object.values(SelectionAreaType as { [key: string]: string }).includes(stitchState.value.tool as string);
    const lensSize = stitchState.value.lensSize?.[0] ?? 0;
    layers.value.forEach((layer) => {
      if (layer.uniform && layer.uniform.uRadius) {
        layer.uniform.uRadius.value = selectionActive ? Math.max(0, lensSize) : Number.MAX_VALUE;
      }
    });
     },
  { immediate: true },
);

// initial availability check once baseSrc is defined
checkDomBaseAvailable();

// Reload if workspace changes
watch(() => appState.workspace, () => loadGrayscaleImages(), { deep: true });

function rotateBox(index: number) {
  const img = greyscaleImages.value[index];
  // increment by 90 and normalize into [-180, 180] for consistent UI display
  const next = (Number(img.rotation) || 0) + 90;
  const normalized = ((next + 180) % 360) - 180;
  img.rotation = normalized;
  // announce rotation change so controls can update
  try {
    window.dispatchEvent(new CustomEvent('stitch:grayscale-prop-changed', { detail: { index, prop: 'rotation', value: normalized } }));
  } catch (e) {
    // ignore
  }
}


function onImageMouseMove(e: MouseEvent) {
  const rect = glcontainer.value?.getBoundingClientRect();
  if (!rect) return;

  // Dragging
  if (draggingIndex.value !== null) {
    const img = greyscaleImages.value[draggingIndex.value];
    img.x = e.clientX - rect.left - dragOffset.value.x;
    img.y = e.clientY - rect.top - dragOffset.value.y;
    // notify other components (e.g. StitchWindow) about the updated position
    try {
      window.dispatchEvent(new CustomEvent('stitch:grayscale-pos-changed', { detail: { index: draggingIndex.value, x: img.x, y: img.y } }));
    } catch (err) {
      // ignore dispatch errors
    }
  }
}

function stopInteractions() {
  draggingIndex.value = null;
}

/**
 * Resets the viewport to a home position such that the entire painting is visible.
 */
async function resetViewport() {
  const size = await getTargetSize();
  const fill = 0.9;
  viewport.center.x = size.width / 2;
  viewport.center.y = size.height / 2;
  viewport.zoom = Math.max(Math.log(size.width / width.value / fill), Math.log(size.height / height.value / fill));
  
}

const dragging = ref(false);

/**
 * Event handler for the onClick event on the glcanvas.
 * @param event - The mouse event.
 */
function onClick(event: MouseEvent) {
  if (event.button == 2) {
    // Prevent opening of context menu.
    event.preventDefault();
  }
}

/**
 * Event handler for the onMouseDown event on the glcanvas.
 * @param event - The mouse event.
 */
function onMouseDown(event: MouseEvent, index: number) {
  if (event.button == 0) {
    startDrag(index, event);
  } else if (event.button == 2) {
    rotateBox(index);
    event.preventDefault();
  }
  selectedIdx.value = index
}

/**
 * Event handler for the onMouseUp event on the glcanvas.
 * @param event - The mouse event.
 */
function onMouseUp(event: MouseEvent) {
  if (event.button == 0) {
    dragging.value = false;
  } else if (event.button == 2 && selectionToolActive.value) {
    dragging.value = false;
  }
}

/**
 * Event handler for the onMouseLeave event on the glcanvas.
 */
function onMouseLeave() {
  dragging.value = false;
}

/**
 * Event handler for the onMouseMove event on the glcanvas.
 * Modifies the viewport if the mouse is pressed down.
 * @param event The event containing the movement of the mouse.
 */
function onMouseMove(event: MouseEvent) {
  if (dragging.value) {
    const scale = Math.exp(viewport.zoom) * stitchState.value.movementSpeed[0];
    viewport.center.x -= event.movementX * scale;
    viewport.center.y += event.movementY * scale;
  }
}

/**
 * Event handler for the onWheel event on the glcanvas.
 * Modifies the viewport to allow zooming in and out on the painting.
 * The zoom gets clamped to a reasonable range.
 * @param event The wheel event containing the amount that was scrolled.
 */
function onWheel(event: WheelEvent) {
  viewport.zoom += (event.deltaY / 500.0) * stitchState.value.scrollSpeed[0];

  // Clamp zoom to a reasonable range
  if (viewport.zoom >= config.imageViewer.zoomLimit || viewport.zoom <= -config.imageViewer.zoomLimit) {
    viewport.zoom = Math.min(config.imageViewer.zoomLimit, Math.max(-config.imageViewer.zoomLimit, viewport.zoom));
    if (!zoomLimitReached) {
      toast.info("Zoom limit reached");
      // Prevent the toast from being shown multiple times
      zoomLimitReached = true;
    }
  } else {
    zoomLimitReached = false;
     }
}

// Move the images using arrow keys
function onKeyDown(event: KeyboardEvent) {
  if (event.key == "ArrowLeft") {
    greyscaleImages.value[selectedIdx.value].x--;
    event.preventDefault();
    event.stopPropagation();
    try { window.dispatchEvent(new CustomEvent('stitch:grayscale-pos-changed', { detail: { index: selectedIdx.value, x: greyscaleImages.value[selectedIdx.value].x, y: greyscaleImages.value[selectedIdx.value].y } })); } catch(e) {}
  } else if (event.key == "ArrowRight") {
    greyscaleImages.value[selectedIdx.value].x++;
    event.preventDefault();
    event.stopPropagation();
    try { window.dispatchEvent(new CustomEvent('stitch:grayscale-pos-changed', { detail: { index: selectedIdx.value, x: greyscaleImages.value[selectedIdx.value].x, y: greyscaleImages.value[selectedIdx.value].y } })); } catch(e) {}
  } else if (event.key == "ArrowUp") {
    greyscaleImages.value[selectedIdx.value].y--;
    event.preventDefault();
    event.stopPropagation();
    try { window.dispatchEvent(new CustomEvent('stitch:grayscale-pos-changed', { detail: { index: selectedIdx.value, x: greyscaleImages.value[selectedIdx.value].x, y: greyscaleImages.value[selectedIdx.value].y } })); } catch(e) {}
  } else if (event.key == "ArrowDown") {
    greyscaleImages.value[selectedIdx.value].y++;
    event.preventDefault();
    event.stopPropagation();
    try { window.dispatchEvent(new CustomEvent('stitch:grayscale-pos-changed', { detail: { index: selectedIdx.value, x: greyscaleImages.value[selectedIdx.value].x, y: greyscaleImages.value[selectedIdx.value].y } })); } catch(e) {}
  }
}

/**
 * Determines the current cursor that should be used in the image viewer.
 */
const cursor = computed(() => {
return dragging.value ? "grabbing" : "grab";
});
</script>

<template>
 <div
    ref="glcontainer"
    class="relative size-full"
    :style="{
      cursor: cursor,
    }"
    @click="onClick"
    @contextmenu="onClick"
    @dblclick="resetViewport"
    @mouseup="onMouseUp"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
    @wheel="onWheel"
    @mousemove.stop="onImageMouseMove"
    @mouseup.stop="stopInteractions"
  >
  <canvas ref="glcanvas" class="absolute inset-0 w-full h-full" />

    

    <!-- Base image (DOM fallback) -->
    <div
      v-if="baseSrc && showDomBase"
      class="absolute inset-0 pointer-events-none flex items-center justify-center"
      :style="{ zIndex: 0, paddingTop: basePadding + 'px', paddingBottom: basePadding + 'px', backgroundColor: 'white', opacity: baseOpacity }"
    >
      <img
        :src="baseSrc"
        class="w-full object-contain"
        :style="{ maxHeight: `calc(100% - ${basePadding * 2}px)`, opacity: baseOpacity }"
        alt="base image"
          @load="onDomBaseLoad"
          @error="onDomBaseError"
      />
    </div>

    <!-- Loading overlay while base GL image is being prepared -->
    <div v-if="baseSrc && !baseReady" class="absolute inset-0 flex items-center justify-center bg-black/40 text-white" style="z-index:30">
      <div class="p-4 bg-black/60 rounded">Loading base image...</div>
    </div>

  

    <div
      v-for="(img, index) in greyscaleImages"
      :key="index"
      class="absolute transition-transform duration-75"
      :style="{
        top: img.y + 'px',
        left: img.x + 'px',
        width: img.width + 'px',
        height: img.height + 'px',
        zIndex: 10,
        opacity: img.opacity ?? baseOpacity,
        transform: `rotate(${img.rotation}deg)`,
      }"
      :class="['border', index === selectedIdx ? 'border border-yellow-500' : 'border-transparent']"

      
      @mousedown.stop="startDrag(index, $event)"
      @mousedown="onMouseDown($event, index)"
      >
        <img
          :src="img.src"
          class="w-full h-full object-contain pointer-events-none"
          :alt="img.name"
        >
      </div>
    </div>

    <Stitchbar v-model:state="stitchState" @reset-viewport="resetViewport" />
  </template>