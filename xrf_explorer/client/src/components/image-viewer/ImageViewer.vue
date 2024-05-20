<script setup lang="ts">
import { Toolbar } from "@/components/image-viewer";
import { inject, onMounted, ref } from "vue";
import { ToolState } from "./types";
import { useResizeObserver } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { layers } from "./state";
import * as THREE from "three";
import { scene } from "./scene";

import fragment from "./fragment.glsl?raw";
import vertex from "./vertex.glsl?raw";

const config = inject<FrontendConfig>("config")!;

// TODO: is it worth it to try to define these constants in one
// place where fragment.glsl can also access them?
/* eslint-disable @typescript-eslint/no-unused-vars */
const TRANSPARENT = 0x00;
const WHOLE = 0x01;
const IN_LENS = 0x02;
const OUTSIDE_LENS = 0x03;
/* eslint-enable @typescript-eslint/no-unused-vars */

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
  movementSpeed: [config.imageViewer.defaultMovementSpeed],
  scrollSpeed: [config.imageViewer.defaultScrollSpeed],
  lensSize: [100.0],
  // TODO: hook this up to layer system
  lensOn: true,
});

let camera: THREE.OrthographicCamera;
let renderer: THREE.WebGLRenderer;

let width: number;
let height: number;

type Point2D = { x: number; y: number };

/**
 * Set up the renderer after mounting the canvas.
 */
onMounted(setup);

/**
 * Update the width and height variables to represent the size of the render target (the glcanvas element).
 */
useResizeObserver(glcontainer, (entries) => {
  const entry = entries[0];
  ({ width, height } = entry.contentRect);
});

/**
 * Sets up the a very basic scene in THREE for rendering.
 */
function setup() {
  camera = new THREE.OrthographicCamera();
  renderer = new THREE.WebGLRenderer({
    alpha: true,
    canvas: glcanvas.value!,
  });

  ({ width, height } = glcontainer.value!.getBoundingClientRect());

  render();
}

/**
 * Sets the uniforms correctly and renders a frame in the renderer.
 */
function render() {
  // Calculate viewport parameters
  const w = width * Math.exp(viewport.zoom);
  const h = height * Math.exp(viewport.zoom);
  const x = viewport.center.x - w / 2;
  const y = viewport.center.y - h / 2;

  layers.value.forEach((layer) => {
    layer.uniform.iViewport.value.set(x, y, w, h);
  });

  renderer.setSize(width, height);
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
  const mouseX = event.layerX;
  const mouseY = event.layerY;
  // Map mouse coordinates to [0,width] and [0,height],
  // reversing y-axis to have (0,0) at top left
  const normalizedX = (width * mouseX) / rect.width;
  const normalizedY = height * (1 - mouseY / rect.height);

  // TODO: should we update this for every layer or only at the relevant ones
  Object.keys(layers).forEach((layer) => {
    layers[layer].uniform!.uMouse.value.set(normalizedX, normalizedY);
    // TODO: should we do this based on the zoom level or not?
    layers[layer].uniform!.uRadius.value = toolState.value.lensSize[0] / viewport.zoom;
  });
}

/**
 * Event handler for the onWheel event on the glcanvas.
 * Modifies the viewport to allow zooming in and out on the painting.
 * @param event The wheel event containing the amount that was scrolled.
 */
function onWheel(event: WheelEvent) {
  viewport.zoom += (event.deltaY / 500.0) * toolState.value.scrollSpeed[0];

  // TODO: should we update this for every layer or only at the relevant ones
  Object.keys(layers).forEach((layer) => {
    // TODO: should we do this based on the zoom level or not?
    layers[layer].uniform!.uRadius.value = toolState.value.lensSize[0] / viewport.zoom;
  });
}
</script>

<template>
  <Toolbar v-model:state="toolState" />
  <div
    ref="glcontainer"
    class="size-full"
    :class="{
      'cursor-grab': !dragging,
      'cursor-grabbing': dragging,
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
  </div>
</template>
