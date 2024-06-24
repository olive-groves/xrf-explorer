import { appState, datasource } from "@/lib/appState";
import { WorkspaceConfig } from "@/lib/workspace";
import { computed, watch } from "vue";
import { createLayer, layerGroups, updateLayerGroupLayers } from "./state";
import { LayerType } from "./types";
import { loadLayerFromTexture, scene } from "./scene";
import { ElementSelection } from "@/lib/selection";
import { layerGroupDefaults } from "./workspace";
import { registerLayer } from "./registering";
import { getDataSize, getRecipe, getTargetSize } from "./api";
import { config } from "@/main";
import * as THREE from "three";
import { hexToRgb } from "@/lib/utils";

import elementalFragment from "./elementalFragment.glsl?raw";
import elementalVertex from "./elementalVertex.glsl?raw";

const selection = computed(() => appState.selection.elements);

/**
 * Represents an elemental map loaded in elementalScene.
 */
type ElementalMap = {
  loading: boolean;
  mesh?: THREE.Mesh;
  uniform: ElementalUniform;
};

/**
 * Uniforms used for rendering an elemental map.
 */
type ElementalUniform = {
  iThreshold: { value: THREE.Vector2 };
  iColor: { value: THREE.Vector3 };
  tMap?: { value: THREE.Texture; type: "t" };
};

// Elemental maps
let elementalMaps: {
  [key: number]: ElementalMap;
} = {};

// THREE js scene object that stores the elemental maps
const elementalScene = new THREE.Scene();

// Render targets that the elemental maps will be rendered to.
const elementalTarget = new THREE.WebGLRenderTarget(1, 1, {
  format: THREE.RGBAFormat,
  type: THREE.FloatType,
});
const elementalAlphaTarget = new THREE.WebGLRenderTarget(1, 1, {
  format: THREE.RGBAFormat,
  type: THREE.FloatType,
});
const elementalCamera = new THREE.OrthographicCamera();

watch(selection, selectionUpdated, { immediate: true, deep: true });

/**
 * Update image viewer to show updated selection.
 * @param newSelection - The updated selection.
 */
function selectionUpdated(newSelection: ElementSelection[]) {
  if (newSelection == undefined) return;
  newSelection.forEach((channel) => {
    const map = elementalMaps[channel.channel];
    if (channel.selected) {
      if (!map.loading && map.mesh == undefined) {
        // Load unloaded selected maps.
        loadMap(channel);
      }

      // Set the uniforms of the map to contain the selected color and thresholds.
      map.uniform.iColor.value.set(...hexToRgb(channel.color));
      map.uniform.iThreshold.value.set(Math.min(...channel.thresholds), Math.max(...channel.thresholds));
    } else {
      if (map.mesh != undefined) {
        // Dispose of deselected maps
        disposeMap(channel.channel);
      }
    }
  });

  // Rerender the elemental maps after the selection has changed.
  requestAnimationFrame(render);
}

/**
 * Loads an elemental map into elementalScene.
 * @param element - The element for which the map should be loaded.
 */
function loadMap(element: ElementSelection) {
  console.debug(`Loading elemental map ${element.channel}`);
  const map = elementalMaps[element.channel];
  map.loading = true;
  const url = `${config.api.endpoint}/${datasource.value}/data/elements/map/${element.channel}`;
  new THREE.TextureLoader().loadAsync(url).then(
    (texture) => {
      texture.colorSpace = THREE.NoColorSpace;

      // Set the texture uniform for the elemental map
      map.uniform.tMap = {
        type: "t",
        value: texture,
      };

      // Create a square
      const shape = new THREE.Shape();
      shape.moveTo(0, 0);
      shape.lineTo(1, 0);
      shape.lineTo(1, 1);
      shape.lineTo(0, 1);

      // Create the geometry
      const geometry = new THREE.ShapeGeometry(shape);

      // Create the shader material that will render the map
      const material = new THREE.RawShaderMaterial({
        fragmentShader: elementalFragment,
        vertexShader: elementalVertex,
        glslVersion: "300 es",
        uniforms: map.uniform,
        side: THREE.DoubleSide,
        transparent: true,
        blending: THREE.AdditiveBlending,
      });

      // Store the mesh
      map.mesh = new THREE.Mesh(geometry, material);
      map.loading = false;

      // Add the elemental map to the scene
      elementalScene.add(map.mesh);

      // Rerender elemental maps after adding new map to the scene.
      requestAnimationFrame(render);
    },
    () => {
      map.loading = false;
    },
  );
}

/**
 * Disposes elemental map from elementalScene.
 * @param channel - The channel of the map to remove.
 */
function disposeMap(channel: number) {
  const map = elementalMaps[channel];
  if (map.mesh != undefined) {
    // Remove the map from the scene
    const uuid = map.mesh.uuid;
    const child = elementalScene.children.filter((mesh) => mesh.uuid == uuid)[0];
    elementalScene.remove(child);

    // Gather some typed variables
    const mesh = child as THREE.Mesh;
    const material = mesh.material as THREE.RawShaderMaterial;
    const uniforms = material.uniforms as ElementalUniform;

    // Remove the texture associated with the map
    uniforms.tMap?.value.dispose();
    uniforms.tMap = undefined;

    // Remove the material and geometry
    material.dispose();
    mesh.geometry.dispose();

    // Remove the last reference to the mesh
    map.mesh = undefined;
  }
}

/**
 * Renders the elemental maps to the render target using order independent transparency.
 */
function render() {
  if (scene.renderer != undefined) {
    // Accumulate all color values in elementalTarget, large values possible due to FloatType.
    // Every layer adds intensity * color to the rgb channels and intensity to the alpha channel.
    // Fragment.glsl will compute the final color as color / sum of intensities.
    scene.renderer.setRenderTarget(elementalTarget);
    Object.values(elementalMaps).forEach((map) => {
      if (map.mesh != undefined) {
        const material = map.mesh.material as THREE.RawShaderMaterial;
        material.blending = THREE.AdditiveBlending;
        material.needsUpdate = true;
      }
    });
    scene.renderer.render(elementalScene, elementalCamera);

    // Render all layers again to calculate maximum intensity at each pixel
    // Will be drawn to elementAlphaTarget which fragment.glsl can access as tAuxiliary
    scene.renderer.setRenderTarget(elementalAlphaTarget);
    Object.values(elementalMaps).forEach((map) => {
      if (map.mesh != undefined) {
        const material = map.mesh.material as THREE.RawShaderMaterial;
        material.blending = THREE.CustomBlending;
        material.blendEquation = THREE.MaxEquation;
        material.blendSrc = THREE.SrcAlphaFactor;
        material.blendDst = THREE.DstAlphaFactor;
        material.needsUpdate = true;
      }
    });
    scene.renderer.render(elementalScene, elementalCamera);

    scene.renderer.setRenderTarget(null);
  }
}

/**
 * Loads the workspace into the layer system.
 * @param workspace - The workspace to load into the layer system.
 */
export async function createElementalLayers(workspace: WorkspaceConfig) {
  if (workspace.elementalCubes.length == 0) return;

  const recipe = await getRecipe(`${config.api.endpoint}/${datasource.value}/data/recipe`);
  recipe.movingSize = await getDataSize();
  recipe.targetSize = await getTargetSize();

  // Setup elemental maps
  Object.keys(elementalMaps).forEach((key) => {
    // Dispose of all previous maps
    disposeMap(parseInt(key));
  });
  elementalMaps = {};
  workspace.elementalChannels.forEach((channel) => {
    elementalMaps[channel.channel] = {
      loading: false,
      uniform: {
        iColor: { value: new THREE.Vector3() },
        iThreshold: { value: new THREE.Vector2() },
      },
    };
  });

  // Setup rendering
  const size = await getDataSize();
  elementalTarget.setSize(size.width, size.height);
  elementalAlphaTarget.setSize(size.width, size.height);
  const layer = createLayer("elemental_maps", "", false);
  layer.uniform.iLayerType.value = LayerType.Elemental;
  layer.uniform.tAuxiliary = { value: elementalAlphaTarget.texture, type: "t" };
  loadLayerFromTexture(layer, elementalTarget.texture);
  registerLayer(layer, recipe);

  // Create layer group
  layerGroups.value.elemental = {
    name: "Elemental maps",
    description: "Generated layer",
    layers: [layer],
    index: -2,
    visible: true,
    ...layerGroupDefaults,
  };

  updateLayerGroupLayers(layerGroups.value.elemental);
}
