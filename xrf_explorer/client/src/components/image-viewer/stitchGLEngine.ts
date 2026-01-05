import * as THREE from "three";
import fragment from "./fragment.glsl?raw";
import vertex from "./vertex.glsl?raw";
import { Layer, LayerType, LayerVisibility } from "./types";

/**
 * A completely independent GL environment for stitching viewers.
 */
export interface StitchEngine {
  scene: THREE.Scene;
  renderer: THREE.WebGLRenderer;
  camera: THREE.OrthographicCamera;
  layers: Layer[];

  /**
   * Create an image layer
   * Returns the created Layer when the texture is loaded.
   */
  createImageLayer(
    id: string,
    imageUrl: string,
    geometrySize?: { width: number; height: number },
    rotation?: number,
  ): Promise<Layer>;
  /**
   * Dispose all GPU resources used by this engine.
   */
  dispose(): void;
}

/**
 * Create a new, completely independent GL engine bound to the given canvas.
 */
export function createStitchEngine(canvas: HTMLCanvasElement): StitchEngine {
  const scene = new THREE.Scene();
  const renderer = new THREE.WebGLRenderer({ alpha: true, canvas });
  const camera = new THREE.OrthographicCamera();
  camera.position.set(0, 0, 10);
  camera.lookAt(0, 0, 0);
  const layers: Layer[] = [];


  async function createImageLayer(
      id: string,
      imageUrl: string,
      geometrySize?: { width: number; height: number },
      rotation?: number,
    ): Promise<Layer> {
    console.debug("[stitch] Creating layer", id, imageUrl);

    const layer: Layer = {
      id,
      image: imageUrl,
      geometrySize,
      rotation,
      uniform: {
        iIndex: { value: 0 },
        iLayerType: { value: LayerType.Image },
        iViewport: { value: new THREE.Vector4() },
        mRegister: { value: new THREE.Matrix3().identity() },
        iShowLayer: { value: LayerVisibility.Visible },
        uOpacity: { value: 1 },
        uContrast: { value: 1 },
        uSaturation: { value: 1 },
        uGamma: { value: 1 },
        uBrightness: { value: 0 },
        uMouse: { value: new THREE.Vector2() },
        uRadius: { value: 0 },
      },
    };

    layers.push(layer);

    // Load texture and build mesh with SAME shader + uniforms as main viewer.
    const texture = await loadTexture(imageUrl);
    await loadLayerIntoEngine(scene, layer, texture);

    return layer;
  }

  function dispose() {
    layers.forEach((layer) => {
      if (layer.mesh) {
        layer.mesh.geometry.dispose();
        (layer.mesh.material as THREE.Material).dispose();
        scene.remove(layer.mesh);
      }
    });
    layers.length = 0;
    renderer.dispose();
  }

  return {
    scene,
    renderer,
    camera,
    layers,
    createImageLayer,
    dispose,
  };
}

// internal helpers

function loadTexture(url: string): Promise<THREE.Texture> {
  return new Promise((resolve, reject) => {
    const loader = new THREE.TextureLoader();
    loader.load(
      url,
      (tex) => {
        tex.colorSpace = THREE.NoColorSpace;
        resolve(tex);
      },
      undefined,
      (err) => reject(err),
    );
  });
}

async function loadLayerIntoEngine(
  localScene: THREE.Scene,
  layer: Layer,
  texture: THREE.Texture,
) {
  // Create a unit square shape
  const shape = new THREE.Shape();
  shape.moveTo(0, 0);
  shape.lineTo(1, 0);
  shape.lineTo(1, 1);
  shape.lineTo(0, 1);

  const geometry = new THREE.ShapeGeometry(shape);

  // Scale the square to targetSize
  const imageWidth =
    layer.geometrySize?.width ?? texture.image.width;

  const imageHeight =
    layer.geometrySize?.height ?? texture.image.height;

  const mat = new THREE.Matrix4();
  mat.set(
    imageWidth, 0,           0, 0,
    0,          imageHeight, 0, 0,
    0,          0,           1, 0,
    0,          0,           0, 1,
  );
  geometry.applyMatrix4(mat);

  // rotate around image center if requested
  if (layer.rotation && layer.rotation !== 0) {
    // move to origin
    geometry.translate(-imageWidth / 2, -imageHeight / 2, 0);
    // rotate
    geometry.rotateZ(layer.rotation);
    // move back
    geometry.translate(imageWidth / 2, imageHeight / 2, 0);
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();
  }

  geometry.computeBoundingBox();
  const bb = geometry.boundingBox!;

  // shift geometry so bottom-left becomes (0,0)
  geometry.translate(-bb.min.x, -bb.min.y, 0);
  geometry.computeBoundingBox();

  // Attach texture to uniforms
  (layer.uniform as any).tImage = {
    type: "t",
    value: texture,
  };

  // Same shader pipeline as main viewer
  const material = new THREE.RawShaderMaterial({
    vertexShader: vertex,
    fragmentShader: fragment,
    glslVersion: "300 es",
    uniforms: layer.uniform,
    side: THREE.DoubleSide,
    transparent: true,
    blending: THREE.NormalBlending,
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.matrixAutoUpdate = true;

  // initial render order like main system
  mesh.renderOrder = -layer.uniform.iIndex.value;

  layer.mesh = mesh;
  localScene.add(mesh);
}