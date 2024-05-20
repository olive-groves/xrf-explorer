import * as THREE from "three";
import { Layer, LayerUniform } from "./types";

export const scene: {
  /**
   * The scene that is being rendered.
   */
  scene: THREE.Scene;
} = {
  scene: new THREE.Scene(),
};

import fragment from "./fragment.glsl?raw";
import vertex from "./vertex.glsl?raw";

/**
 * Creates a layer and adds the given image to it.
 * @param layer - The layer that should get loaded.
 */
export function loadLayer(layer: Layer) {
  new THREE.TextureLoader().loadAsync(layer.url).then((texture) => {
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
      transparent: true,
      blending: THREE.NormalBlending,
    });

    const mesh = new THREE.Mesh(geometry, material);

    layer.mesh = mesh;

    scene.scene.add(mesh);
  });
}

/**
 * Disposes a layer from the GPU, freeing up memory.
 * Does not remove the layer from the layers.
 * @param layer - The layer to dispose of.
 */
export function disposeLayer(layer: Layer) {
  if (layer.mesh != undefined) {
    const uuid = layer.mesh.uuid;
    const child = scene.scene.children.filter((mesh) => mesh.uuid == uuid)[0];
    scene.scene.remove(child);

    const mesh = child as THREE.Mesh;
    const material = mesh.material as THREE.RawShaderMaterial;
    const uniforms = material.uniforms as LayerUniform;

    uniforms.tImage?.value.dispose();
    uniforms.tImage = undefined;

    material.dispose();
    mesh.geometry.dispose();

    layer.mesh = undefined;
  }
}
