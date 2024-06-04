<script setup lang="ts">
import { Toolbar } from "@/components/image-viewer";
import { computed, inject, onMounted, ref } from "vue";
import { ToolState } from "./types";
import { useElementBounding } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { layers } from "./state";
import * as THREE from "three";
import { scene } from "./scene";
import { toast } from "vue-sonner";

const config = inject<FrontendConfig>("config")!;

const glcontainer = ref<HTMLDivElement | null>(null);
const glcanvas = ref<HTMLCanvasElement | null>(null);

const viewport: {
  center: { x: number; y: number };
  zoom: number;
} = {
  center: { x: 4000, y: 3000 },
  zoom: 2,
};

const toolState = ref<ToolState>({
  tool: "grab",
  movementSpeed: [config.imageViewer.defaultMovementSpeed],
  scrollSpeed: [config.imageViewer.defaultScrollSpeed],
  lensSize: [config.imageViewer.defaultLensSize],
});

let camera: THREE.OrthographicCamera;
let renderer: THREE.WebGLRenderer;

const canvasSize = useElementBounding(glcontainer);
const width = canvasSize.width;
const height = canvasSize.height;

// Flag to prevent the zoom limit toast from being shown multiple times
let zoomLimitReached = false;

/**
 * Set up the renderer after mounting the canvas.
 */
onMounted(setup);

/**
 * Sets up the very basic scene in THREE for rendering.
 */
function setup() {
  camera = new THREE.OrthographicCamera();
  renderer = new THREE.WebGLRenderer({
    alpha: true,
    canvas: glcanvas.value!,
  });

  render();
}

/**
 * Sets the uniforms correctly and renders a frame in the renderer.
 */
function render() {
  // Calculate viewport parameters
  const w = width.value * Math.exp(viewport.zoom);
  const h = height.value * Math.exp(viewport.zoom);
  const x = viewport.center.x - w / 2;
  const y = viewport.center.y - h / 2;
  const lensSize = toolState.value.tool == "lens" ? toolState.value.lensSize[0] : Number.MAX_VALUE;

  layers.value.forEach((layer) => {
    layer.uniform.iViewport.value.set(x, y, w, h);
    layer.uniform.uRadius.value = lensSize;
  });

  renderer.setSize(width.value, height.value);
  renderer.render(scene.scene, camera);

  requestAnimationFrame(render);
}

const dragging = ref(false);

/**
 * Event handler for the onMouseDown event on the glcanvas.
 */
function onMouseDown() {
  dragging.value = true;
}

/**
 * Event handler for the onMouseUp event on the glcanvas.
 */
function onMouseUp() {
  dragging.value = false;
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
    const scale = Math.exp(viewport.zoom) * toolState.value.movementSpeed[0];
    viewport.center.x -= event.movementX * scale;
    viewport.center.y += event.movementY * scale;
  }

  const rect = glcanvas.value!.getBoundingClientRect();
  const mouseX = event.clientX - canvasSize.left.value;
  const mouseY = event.clientY - canvasSize.top.value;

  // Map mouse coordinates to [0,width] and [0,height],
  // reversing y-axis to have (0,0) at top left
  const normalizedX = (width.value * mouseX) / rect.width;
  const normalizedY = height.value * (1 - mouseY / rect.height);

  layers.value.forEach((layer) => {
    layer.uniform.uMouse.value.set(normalizedX, normalizedY);
  });
}

/**
 * Event handler for the onWheel event on the glcanvas.
 * Modifies the viewport to allow zooming in and out on the painting.
 * The zoom gets clamped to a reasonable range.
 * @param event The wheel event containing the amount that was scrolled.
 */
function onWheel(event: WheelEvent) {
  viewport.zoom += (event.deltaY / 500.0) * toolState.value.scrollSpeed[0];

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

/**
 * Determines the current cursor that should be used in the image viewer.
 */
const cursor = computed(() => {
  if (toolState.value.tool == "lens") {
    return "crosshair";
  } else {
    return dragging.value ? "grabbing" : "grab";
  }
});
</script>

<template>
  <div
    ref="glcontainer"
    class="relative size-full"
    :style="{
      cursor: cursor,
    }"
  >
    <canvas
      ref="glcanvas"
      @mousedown="onMouseDown"
      @mouseup="onMouseUp"
      @mouseleave="onMouseLeave"
      @mousemove="onMouseMove"
      @wheel="onWheel"
    />
    <Toolbar v-model:state="toolState" />
  </div>
</template>
