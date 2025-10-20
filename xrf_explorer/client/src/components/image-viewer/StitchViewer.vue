<script setup lang="ts">
import { Stitchbar } from "@/components/image-viewer";
import { computed, inject, onBeforeUnmount, ref, onMounted, watch, nextTick } from "vue";
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
}

const dummyImages = ref<ImageBox[]>([]);
const selectedIdx = ref(0);

const draggingIndex = ref<number | null>(null);
const dragOffset = ref({ x: 0, y: 0 });

onMounted(() => {
  window.addEventListener("keydown", onKeyDown);
  // Ensure we have latest workspace so grayscale entries are visible
  ensureWorkspaceHasGrayscale().then(async () => {
    await setupGL();
    await loadGrayscaleImages();
  });
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeyDown);
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
  const img = dummyImages.value[index];
  const rect = glcontainer.value?.getBoundingClientRect();
  if (!rect) return;

  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  dragOffset.value = {
    x: mouseX - img.x,
    y: mouseY - img.y
  };
}

// Helpers to load grayscale images from workspace
import { appState } from "@/lib/appState";
import { getImageSize } from "./api";
import { getWorkspaceImageUrl } from "./workspace";
import { computed as vueComputed } from "vue";
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
  dummyImages.value = [];
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

    dummyImages.value.push({
      name: g.name || `grayscale_${i}`,
      src,
      x,
      y,
      width: w,
      height: h,
      rotation: 0,
    });
  }

  // Also create GL layers for the grayscales
  try {
    // create base layer if not present
    createOrUpdateBaseLayer();

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
  } catch (e) {
    console.warn("Could not create GL grayscale layers", e);
  }
}

/** Ensure the GL base layer exists and is attached to a layer group */
function createOrUpdateBaseLayer() {
  const ws = appState.workspace;
  if (!ws || !ws.baseImage) return;
  const baseLoc = (ws.baseImage as any).imageLocation ?? ws.baseImage.name;
  const baseUrl = getWorkspaceImageUrl(baseLoc, ws.name);
  const baseId = `base_${(ws.baseImage.name || "base").replace(/\s+/g, "_")}`;
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
        // keep lens off by default
        layer.uniform.uRadius.value = Number.MAX_VALUE;
      }
    });

    // ensure renderer size matches container
    scene.renderer!.setSize(width.value, height.value);

    // Sync DOM tile positions to GL meshes
    try {
      for (let i = 0; i < dummyImages.value.length; i++) {
        const img = dummyImages.value[i];
        const id = `stitch_gray_${img.name}`;
        const layer = layers.value.find((l) => l.id === id);
        if (layer && layer.mesh) {
          // Position mesh at top-left of the image (mesh geometry is in pixel coords)
          layer.mesh.position.set(img.x, img.y, 0);
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
        const baseId = `base_${(ws.baseImage.name || "base").replace(/\s+/g, "_")}`;
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

    // Render the shared scene with our camera
    if (camera) {
      scene.renderer!.render(scene.scene, camera);
    }

    animationFrame = requestAnimationFrame(render);
  }

  // start
  animationFrame = requestAnimationFrame(render);
}

// Compute base image URL to show as background
const baseSrc = vueComputed(() => {
  const ws = appState.workspace;
  if (!ws || !ws.baseImage) return null;
  // prefer imageLocation if available, fallback to name
  const loc = (ws.baseImage as any).imageLocation ?? ws.baseImage.name;
  return getWorkspaceImageUrl(loc, ws.name);
});

// Reload if workspace changes
watch(() => appState.workspace, () => loadGrayscaleImages(), { deep: true });

function rotateBox(index: number) {
  const img = dummyImages.value[index];
  img.rotation = (img.rotation + 90) % 360;
}


function onImageMouseMove(e: MouseEvent) {
  const rect = glcontainer.value?.getBoundingClientRect();
  if (!rect) return;

  // Dragging
  if (draggingIndex.value !== null) {
    const img = dummyImages.value[draggingIndex.value];
    img.x = e.clientX - rect.left - dragOffset.value.x;
    img.y = e.clientY - rect.top - dragOffset.value.y;
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
    dummyImages.value[selectedIdx.value].x--;
    event.preventDefault();
    event.stopPropagation();
  } else if (event.key == "ArrowRight") {
    dummyImages.value[selectedIdx.value].x++;
    event.preventDefault();
    event.stopPropagation();
  } else if (event.key == "ArrowUp") {
    dummyImages.value[selectedIdx.value].y--;
    event.preventDefault();
    event.stopPropagation();
  } else if (event.key == "ArrowDown") {
    dummyImages.value[selectedIdx.value].y++;
    event.preventDefault();
    event.stopPropagation();
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
  <div>Selected Image: {{ selectedIdx + 1 }}</div>
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
    <canvas ref="glcanvas" />

    <!-- Base image -->
    <div v-if="baseSrc" class="absolute inset-0 pointer-events-none" style="z-index:0">
      <img :src="baseSrc" class="w-full h-full object-contain" alt="base image" />
    </div>

    <div
      v-for="(img, index) in dummyImages"
      :key="index"
      class="absolute transition-transform duration-75"
      :style="{
        top: img.y + 'px',
        left: img.x + 'px',
        width: img.width + 'px',
        height: img.height + 'px',
        zIndex: 10,
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

    <Stitchbar v-model:state="stitchState" @reset-viewport="resetViewport" />
  </div>
</template>
