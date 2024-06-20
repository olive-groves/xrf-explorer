import { appState, datasource } from "@/lib/appState";
import { WorkspaceConfig } from "@/lib/workspace";
import { computed, watch } from "vue";
import { createLayer, layerGroups, layers, updateLayerGroupLayers } from "./state";
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

type ElementalMap = {
  loading: boolean;
  mesh?: THREE.Mesh;
  uniform: ElementalUniform;
};

type ElementalUniform = {
  iThreshold: { value: THREE.Vector2 };
  iColor: { value: THREE.Vector3 };
  tMap?: { value: THREE.Texture; type: "t" };
};

let elementalMaps: {
  [key: number]: ElementalMap;
} = {};
const elementalScene = new THREE.Scene();
const elementalTarget = new THREE.WebGLRenderTarget(1, 1, {
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
  newSelection.forEach((channel) => {
    const map = elementalMaps[channel.channel];
    if (channel.selected) {
      if (!map.loading && map.mesh == undefined) {
        loadMap(channel);
      }
      map.uniform.iColor.value.set(...hexToRgb(channel.color));
      map.uniform.iThreshold.value.set(Math.min(...channel.thresholds), Math.max(...channel.thresholds));
    } else {
      if (map.mesh != undefined) {
        disposeMap(channel.channel);
      }
    }
  });

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

      map.uniform.tMap = {
        type: "t",
        value: texture,
      };

      const shape = new THREE.Shape();
      shape.moveTo(0, 0);
      shape.lineTo(1, 0);
      shape.lineTo(1, 1);
      shape.lineTo(0, 1);

      const geometry = new THREE.ShapeGeometry(shape);

      const material = new THREE.RawShaderMaterial({
        fragmentShader: elementalFragment,
        vertexShader: elementalVertex,
        glslVersion: "300 es",
        uniforms: map.uniform,
        side: THREE.DoubleSide,
        transparent: true,
        blending: THREE.AdditiveBlending,
      });

      map.mesh = new THREE.Mesh(geometry, material);

      map.loading = false;

      elementalScene.add(map.mesh);

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
    const uuid = map.mesh.uuid;
    const child = elementalScene.children.filter((mesh) => mesh.uuid == uuid)[0];
    elementalScene.remove(child);

    const mesh = child as THREE.Mesh;
    const material = mesh.material as THREE.RawShaderMaterial;
    const uniforms = material.uniforms as ElementalUniform;

    uniforms.tMap?.value.dispose();
    uniforms.tMap = undefined;

    material.dispose();
    mesh.geometry.dispose();

    map.mesh = undefined;
  }
}

/**
 * Renders the elemental maps to the render target using order independent transparency.
 */
function render() {
  if (scene.renderer != undefined) {
    scene.renderer.setRenderTarget(elementalTarget);
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
  const layer = createLayer("elemental_maps", "", false);
  layer.uniform.iLayerType.value = LayerType.Elemental;
  loadLayerFromTexture(layer, elementalTarget.texture);
  registerLayer(layer, recipe);

  layerGroups.value.elemental = {
    name: "Elemental maps",
    description: "Generated layer",
    layers: [layer],
    index: -2,
    visible: true,
    ...layerGroupDefaults,
  };

  console.log(layers);

  updateLayerGroupLayers(layerGroups.value.elemental);
}
