<template>
  <div ref="glcontainer" class="w-full h-full">
    <canvas ref="glcanvas" @mousedown="onMouseDown" @mouseup="onMouseUp" @mouseleave="onMouseLeave"
      @mousemove="onMouseMove" @wheel="onWheel" />
  </div>
</template>

<!-- Renderer -->
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import * as THREE from 'three';

import { Layer, LayerUniform } from './types';
import { useResizeObserver } from '@vueuse/core';

const vertex = `
precision highp float;
precision highp int;

uniform float iTime;
uniform vec4 iViewport; // x, y, w, h

attribute vec3 position;
attribute vec2 uv;

varying vec2 vUv;

void main() {
  float scale = 0.5+0.5*cos(iTime);
  scale = 1.0;
  vUv = uv;
  vec2 position = scale*position.xy;

  // Transform to viewport
  gl_Position = vec4(
    2.0 * (position.x - iViewport.x) / iViewport.z - 1.0,
    2.0 * (position.y - iViewport.y) / iViewport.w - 1.0,
    1.0,
    1.0
  );
}`;

const fragment = `
precision highp float;
precision highp int;

uniform vec3 iResolution;
uniform float iTime;
uniform sampler2D tImage;

varying vec2 vUv;

void main() {
  gl_FragColor = texture2D(tImage, vUv);
  vec2 uv = gl_FragCoord.xy / iResolution.xy;
  // gl_FragColor = vec4(vUv, 0.0, 1.0);
}`;

const glcontainer = ref<HTMLDivElement | null>(null);
const glcanvas = ref<HTMLCanvasElement | null>(null);

const viewport: {
  center: { x: number, y: number },
  zoom: number
} = {
  center: { x: 0, y: 0 },
  zoom: 0
}

let scene: THREE.Scene;
let camera: THREE.OrthographicCamera;
let renderer: THREE.WebGLRenderer;

let width: number;
let height: number;

const layers: Layer[] = [];

onMounted(() => {
  setup();

  addLayer("https://upload.wikimedia.org/wikipedia/commons/0/06/Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg");
  // addLayer("https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg/8192px-Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg");

  render(0);
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

function addLayer(image: string) {
  new THREE.TextureLoader().load(image, (texture) => {
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
      texture.image.width, 0, 0, -texture.image.width / 2,
      0, texture.image.height, 0, -texture.image.height / 2,
      0, 0, 1, 0,
      0, 0, 0, 1
    );

    geometry.applyMatrix4(mat);

    const uniform: LayerUniform = {
      iTime: { value: 0 },
      iResolution: { value: new THREE.Vector3 },
      iViewport: { value: new THREE.Vector4 },
      tImage: {
        type: 't',
        value: texture
      }
    };

    const material = new THREE.RawShaderMaterial({
      vertexShader: vertex,
      fragmentShader: fragment,
      uniforms: uniform,
      side: THREE.DoubleSide
    });

    const mesh = new THREE.Mesh(geometry, material);

    scene.add(mesh);

    layers.push({
      image: image,
      mesh: mesh,
      uniform: uniform
    });
  });
}

function render(time: number) {
  // Calculate viewport parameters
  const w = width * Math.exp(viewport.zoom);
  const h = height * Math.exp(viewport.zoom);
  const x = viewport.center.x + w / 2;
  const y = viewport.center.y - h / 2;

  layers.forEach((layer) => {
    layer.uniform!.iTime.value = time * 0.001;
    layer.uniform!.iResolution.value.set(width, height, 1);
    layer.uniform!.iViewport.value.set(
      -x,
      y,
      w,
      h
    );
  });

  renderer.setSize(width, height);
  renderer.render(scene, camera);

  // TODO: Only rerender when required?
  requestAnimationFrame(render);
}

let dragging = false;

function onMouseDown() {
  dragging = true;
}

function onMouseUp() {
  dragging = false;
}

function onMouseLeave() {
  dragging = false;
}

function onMouseMove(event: MouseEvent) {
  if (dragging) {
    const scale = Math.exp(viewport.zoom) * 2.0;
    viewport.center.x += event.movementX * scale;
    viewport.center.y += event.movementY * scale;
  }
}

function onWheel(event: WheelEvent) {
  viewport.zoom += event.deltaY / 500.0;
}
</script>