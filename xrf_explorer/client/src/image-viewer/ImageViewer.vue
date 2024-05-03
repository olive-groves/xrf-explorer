<script setup lang="ts">
import { Toolbar } from '@/image-viewer';
import { onMounted, ref } from 'vue';
import * as THREE from 'three';

import { Layer, ToolState } from './types';
import { useResizeObserver } from '@vueuse/core';

const vertex = `
precision highp float;
precision highp int;

uniform float iIndex;
uniform vec4 iViewport; // x, y, w, h
uniform mat3 mRegister;

attribute vec3 position;
attribute vec2 uv;

varying vec2 vUv;

void main() {
  vUv = uv;

  // Register vertices
  vec3 position = mRegister * vec3(position.xy, 1.0);

  // Transform to viewport
  gl_Position = vec4(
    2.0 * (position.x - iViewport.x) / iViewport.z - 1.0,
    2.0 * (position.y - iViewport.y) / iViewport.w - 1.0,
    iIndex / 1024.0,
    1.0
  );
}`;

const fragment = `
precision highp float;
precision highp int;

uniform sampler2D tImage;

varying vec2 vUv;

void main() {
  gl_FragColor = texture2D(tImage, vUv);
}`;

const glcontainer = ref<HTMLDivElement | null>(null);
const glcanvas = ref<HTMLCanvasElement | null>(null);

const viewport: {
  center: { x: number, y: number },
  zoom: number
} = {
  center: { x: 8191, y: 0 },
  zoom: 0
}

const toolState = ref<ToolState>({
  movementSpeed: [2.0],
  scrollSpeed: [1.0]
});

let scene: THREE.Scene;
let camera: THREE.OrthographicCamera;
let renderer: THREE.WebGLRenderer;

let width: number;
let height: number;

const layers: {
  [key: string]: Layer
} = {};

// const layerStack: string[] = [];

onMounted(() => {
  setup();

  // addLayer("rgb", "https://upload.wikimedia.org/wikipedia/commons/0/06/Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg");
  addLayer("rgb", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg/8192px-Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg");

  render();
});

useResizeObserver(glcontainer, (entries) => {
  const entry = entries[0];
  ({ width, height } = entry.contentRect);
})

function setup() {
  scene = new THREE.Scene();
  camera = new THREE.OrthographicCamera();
  renderer = new THREE.WebGLRenderer({
    alpha: true,
    canvas: glcanvas.value!
  });

  ({ width, height } = glcontainer.value!.getBoundingClientRect());
}

function addLayer(id: string, image: string) {
  const layer: Layer = {
    id: id,
    image: image,
    uniform: {
      iIndex: { value: 0 },
      iViewport: { value: new THREE.Vector4 },
      mRegister: { value: new THREE.Matrix3(1, 0, 0, 0, 1, 0, 0, 0, 1) }
    }
  };


  layers[id] = layer;

  new THREE.TextureLoader().loadAsync(image).then((texture) => {
    texture.colorSpace = THREE.NoColorSpace;

    const shape = new THREE.Shape();

    shape.moveTo(0, 0);
    shape.lineTo(1, 0);
    shape.lineTo(1, 1);
    shape.lineTo(0, 1);

    const geometry = new THREE.ShapeGeometry(shape);

    // Transform geometry in accordance to recipe
    // TODO: Do it according to recipe
    // TODO: Separate this into an independent function to allow updating
    let mat = new THREE.Matrix4();
    mat.set(
      texture.image.width, 0, 0, 0,
      0, texture.image.height, 0, 0,
      0, 0, 1, 0,
      0, 0, 0, 1
    );

    geometry.applyMatrix4(mat);

    layer.uniform.tImage = {
      type: "t",
      value: texture
    };

    const material = new THREE.RawShaderMaterial({
      vertexShader: vertex,
      fragmentShader: fragment,
      uniforms: layer.uniform,
      side: THREE.DoubleSide
    });

    const mesh = new THREE.Mesh(geometry, material);

    layer.mesh = mesh;

    scene.add(mesh);
  });
}

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

  // TODO: Only rerender when required?
  requestAnimationFrame(render);
}

let dragging = ref(false);

function onMouseDown() {
  dragging.value = true;
}

function onMouseUp() {
  dragging.value = false;
}

function onMouseLeave() {
  dragging.value = false;
}

function onMouseMove(event: MouseEvent) {
  if (dragging.value) {
    const scale = Math.exp(viewport.zoom) * toolState.value.movementSpeed[0];
    viewport.center.x -= event.movementX * scale;
    viewport.center.y += event.movementY * scale;
  }
}

function onWheel(event: WheelEvent) {
  viewport.zoom += event.deltaY / 500.0 * toolState.value.scrollSpeed[0];
}
</script>

<template>
  <Toolbar v-model:state="toolState" />
  <div ref="glcontainer" class="w-full h-full" :class="{
    'cursor-grab': !dragging,
    'cursor-grabbing': dragging
  }">
    <canvas ref="glcanvas" @mousedown="onMouseDown" @mouseup="onMouseUp" @mouseleave="onMouseLeave"
      @mousemove="onMouseMove" @wheel="onWheel" />
  </div>
</template>