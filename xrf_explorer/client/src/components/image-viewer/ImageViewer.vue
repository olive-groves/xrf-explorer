<script setup lang="ts">
import { Toolbar } from "@/components/image-viewer";
import { inject, onMounted, ref } from "vue";
import * as THREE from "three";
import * as math from "mathjs";

import { Layer, ToolState } from "./types";
import { useResizeObserver } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";

import fragment from "./fragment.glsl?raw"
import vertex from "./vertex.glsl?raw"

const config = inject<FrontendConfig>("config")!;

// TODO: is it worth it to try to define these constants in one 
// place where fragment.glsl can also access them?
const TRANSPARENT = 0x00;
const WHOLE = 0x01;
const IN_LENS = 0x02;
const OUTSIDE_LENS = 0x03;

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

let scene: THREE.Scene;
let camera: THREE.OrthographicCamera;
let renderer: THREE.WebGLRenderer;

let width: number;
let height: number;

type Point2D = { x: number; y: number };

const layers: {
  [key: number]: Layer;
} = {};

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
  scene = new THREE.Scene();
  camera = new THREE.OrthographicCamera();
  renderer = new THREE.WebGLRenderer({
    alpha: true,
    canvas: glcanvas.value!,
  });

  ({ width, height } = glcontainer.value!.getBoundingClientRect());

  // Temporary, until layer system is in place and can handle the layers programmatically.
  addLayer(
    "bottom",
    //"https://upload.wikimedia.org/wikipedia/commons/0/06/Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/81/Vincent_van_Gogh_-_Two_Crabs_%281889%29.jpg",
  );
  addLayer(
    "mid",
    "https://upload.wikimedia.org/wikipedia/commons/a/a1/Korenveld_met_kraaien_-_s0149V1962_-_Van_Gogh_Museum.jpg",
  );
  addLayer(
    "top",
    "https://upload.wikimedia.org/wikipedia/commons/8/80/Amandelbloesem_-_s0176V1962_-_Van_Gogh_Museum.jpg",
  );

  render();
}

/**
 * Creates a layer and adds the given image to it.
 * @param id - Id given to the layer.
 * @param image - Path to the image to be added.
 */
function addLayer(id: string, image: string) {
  const layer: Layer = {
    id: id,
    image: image,
    uniform: {
      iIndex: { value: 0 },
      iViewport: { value: new THREE.Vector4() },
      // Temporary usage
      iShowLayer: { value: id == "top" ? OUTSIDE_LENS : IN_LENS},
      mRegister: { value: new THREE.Matrix3(1, 0, 0, 0, 1, 0, 0, 0, 1) },
      uMouse: { value: new THREE.Vector2(0.5, 0.5) },
      uRadius: { value: toolState.value.lensSize[0] / viewport.zoom },
    },
  };
  layers[id] = layer;

  new THREE.TextureLoader().loadAsync(image).then((texture) => {
    texture.colorSpace = THREE.NoColorSpace;

    // Create a square
    const shape = new THREE.Shape();
    shape.moveTo(0, 0);
    shape.lineTo(1, 0);
    shape.lineTo(1, 1);
    shape.lineTo(0, 1);

    const geometry = new THREE.ShapeGeometry(shape);

    // Scale the square to the same dimensions as the texture.
    // By scaling through this method, the UV coordinates of the shape are preserved.
    const mat = new THREE.Matrix4();
    mat.set(texture.image.width, 0, 0, 0, 0, texture.image.height, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1);
    geometry.applyMatrix4(mat);

    // Add the texture to the uniform to allow it to be used in the shaders
    layer.uniform.tImage = {
      type: "t",
      value: texture,
    };

    // Create a material to render the texture on to the created shape.
    // The vertex shader handles the movement of the texture for registering and the viewport.
    // The fragment shader handles sampling colors from the texture.
    const material = new THREE.RawShaderMaterial({
      vertexShader: vertex,
      fragmentShader: fragment,
      uniforms: layer.uniform,
      side: THREE.DoubleSide,
      transparent: true, // Enable transparency
      blending: THREE.NormalBlending, // Use normal blending mode
    });

    const mesh = new THREE.Mesh(geometry, material);

    layer.mesh = mesh;

    scene.add(mesh);
  });
}

/**
 * Changes a provided matrix to contain the perspective transform generated from a registering recipe.
 * @param mat - A matrix that will contain the perspective transform.
 * @param src - An array of 4 points representing the source quadrilateral's corners.
 * @param dst - An array of 4 points representing the destination quadrilateral's corners.
 * @param srcWidth - Width of source image.
 * @param srcHeight - Height of source image.
 * @param dstWidth - Width of destination image.
 * @param dstHeight - Height of destination image.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function setPerspectiveTransform(
  mat: THREE.Matrix3,
  src: Point2D[],
  dst: Point2D[],
  srcWidth: number,
  srcHeight: number,
  dstWidth: number,
  dstHeight: number,
) {
  // Unscale the points of the src image
  const scale = Math.min(dstWidth / srcWidth, dstHeight / srcHeight);
  src.forEach((point) => {
    (point.x = point.x / scale), (point.y = point.y / scale);
  });

  // Matrices for Ax=B
  const A = []; // 8 x 8
  const B = []; // 8 x 1
  for (let i = 0; i < 4; i++) {
    A.push([src[i].x, src[i].y, 1, 0, 0, 0, -src[i].x * dst[i].x, -src[i].y * dst[i].x]);
    B.push(dst[i].x);
  }
  for (let i = 0; i < 4; i++) {
    A.push([0, 0, 0, src[i].x, src[i].y, 1, -src[i].x * dst[i].y, -src[i].y * dst[i].y]);
    B.push(dst[i].y);
  }

  // Solve Ax = B and extract solution
  const x = math.lusolve(A, B); // 8 x 1

  mat.set(x[0][0], x[1][0], x[2][0], x[3][0], x[4][0], x[5][0], x[6][0], x[7][0], 1);
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

  Object.keys(layers).forEach((layer) => {
    layers[layer].uniform!.iViewport.value.set(x, y, w, h);
  });

  renderer.setSize(width, height);
  renderer.render(scene, camera);

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
