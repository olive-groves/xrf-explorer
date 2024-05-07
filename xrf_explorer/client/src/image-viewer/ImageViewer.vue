<script setup lang="ts">
import { Toolbar } from '@/image-viewer';
import { onMounted, ref } from 'vue';
import * as THREE from 'three';
import * as math from 'mathjs';

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
  center: { x: 4000, y: 3000 },
  zoom: 2
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

type Point2f = {x: number, y:number}

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
    // TODO: Get recipe and pass it to transformGeometry(...)
    //const src: Point2f[] = [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 1, y: 1 }, { x: 0, y: 1 }];
    //const dst: Point2f[] = [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 1.5, y: 1.5 }, { x: 0, y: 1 }];
    //transformGeometry(geometry, src, dst);

    // Temporary implementation:
    let mat = new THREE.Matrix4();
    mat.set(
      width, 0, 0, 0,
      0, height, 0, 0,
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

function transformGeometry(geometry: THREE.ShapeGeometry, src: Point2f[], dst: Point2f[]) {
  // Matrices for system Ax=B
  const A = []; // 8 x 8
  const B = []; // 8 x 1
  for (let i = 0; i < 4; i++) {
    A.push(
      [src[i].x, src[i].y, 1, 0, 0, 0, -src[i].x * dst[i].x, -src[i].y * dst[i].x],
      [0, 0, 0, src[i].x, src[i].y, 1, -src[i].x * dst[i].y, -src[i].y * dst[i].y]
    );
    B.push(dst[i].x, dst[i].y);
  }

  // Solve Ax = B and extract solution
  const x = math.lusolve(A, B); // 8 x 1

  let mat = new THREE.Matrix4();
  mat.set(
    x[0][0], x[1][0], x[2][0],
    x[3][0], x[4][0], x[5][0],
    x[6][0], x[7][0], 1
  );

  geometry.applyMatrix4(mat);
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
