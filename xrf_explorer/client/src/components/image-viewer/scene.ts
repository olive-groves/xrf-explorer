import * as THREE from "three";
import { Layer, LayerGroup, LayerUniform } from "./types";

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
import { toast } from "vue-sonner";
import { h, markRaw } from "vue";
import { getTargetSize } from "./api";

/**
 * Creates a layer in the image viewer and adds the given image to it.
 * @param layer - The layer that should get loaded.
 * @param interpolated - Whether the sampler should interpolate between pixels.
 */
export function loadLayer(layer: Layer, interpolated: boolean = true) {
  new THREE.TextureLoader().loadAsync(layer.image).then(
    async (texture) => {
      texture.colorSpace = THREE.NoColorSpace;

      // Disable interpolation if required
      if (!interpolated) {
        texture.magFilter = THREE.NearestFilter;
        texture.minFilter = THREE.NearestFilter;
        texture.generateMipmaps = false;
      }

      // Create a square
      const shape = new THREE.Shape();
      shape.moveTo(0, 0);
      shape.lineTo(1, 0);
      shape.lineTo(1, 1);
      shape.lineTo(0, 1);

      const geometry = new THREE.ShapeGeometry(shape);

      // Get the size of the target image
      const size = await getTargetSize();

      // Scale the square to the same dimensions as the texture.
      // By scaling through this method, the UV coordinates of the shape are preserved.
      const mat = new THREE.Matrix4();
      mat.set(size.width, 0, 0, 0, 0, size.height, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1);
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
        glslVersion: "300 es",
        uniforms: layer.uniform,
        side: THREE.DoubleSide,
        transparent: true,
        blending: THREE.NormalBlending,
      });

      const mesh = new THREE.Mesh(geometry, material);

      // Set the correct initial render order.
      mesh.renderOrder = -layer.uniform.iIndex.value;

      layer.mesh = mesh;

      scene.scene.add(mesh);
    },
    (reason) => {
      console.warn(`Failed to load layer ${layer.id}`, reason);
      toast.warning("Failed to load layer", {
        description: markRaw(h("div", ["Request to ", h("code", layer.image), " failed"])),
      });
    },
  );
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

/**
 * Creates a data texture of specified size and format. Every pixel contains 4 bytes of data.
 * @param data - The data array.
 * @param width - The width of the data texture.
 * @param height - The height of the data texture.
 * @returns The datatexture.
 */
export function createDataTexture(data: ArrayBufferView, width: number, height: number): THREE.DataTexture {
  const texture = new THREE.DataTexture(
    data,
    width,
    height,
    THREE.RGBAFormat,
    THREE.UnsignedByteType,
    THREE.UVMapping,
    THREE.ClampToEdgeWrapping,
    THREE.ClampToEdgeWrapping,
    THREE.NearestFilter,
    THREE.NearestFilter,
    1,
    THREE.NoColorSpace,
  );
  texture.needsUpdate = true;
  texture.generateMipmaps = false;
  return texture;
}

/**
 * Update the data texture for every layer in the layergroup.
 * @param group - The group to update.
 */
export function updateDataTexture(group: LayerGroup) {
  group.layers.forEach((layer) => {
    if (layer.mesh != undefined) {
      (layer.mesh!.material as THREE.Material).needsUpdate = true;
    }
    if (layer.uniform.tAuxiliary != undefined) {
      layer.uniform.tAuxiliary!.value.needsUpdate = true;
    }
  });
}
