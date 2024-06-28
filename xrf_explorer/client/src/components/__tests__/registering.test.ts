import { describe, expect, test } from "vitest";
import { registerLayer, RegisteringRecipe } from "../image-viewer/registering";
import { Layer, LayerType, LayerVisibility } from "../image-viewer/types";
import * as THREE from "three";

describe("registerLayer Test", () => {
  const matrix = new THREE.Matrix3();
  matrix.set(1, 2, 3, 4, 5, 6, 7, 8, 9);

  const layer: Layer = {
    id: "anId",
    image: "anImage",
    uniform: {
      iIndex: { value: 0 },
      iLayerType: { value: LayerType.Image },
      iViewport: { value: new THREE.Vector4() },
      mRegister: { value: matrix },
      iShowLayer: { value: LayerVisibility.Visible },
      uOpacity: { value: 1 },
      uContrast: { value: 1 },
      uSaturation: { value: 1 },
      uGamma: { value: 1 },
      uBrightness: { value: 1 },
      uMouse: { value: new THREE.Vector2() },
      uRadius: { value: 1 },
    },
  };

  const recipe: RegisteringRecipe = {
    target: [
      [0, 0],
      [0, 1],
      [1, 0],
      [1, 1],
    ],
    moving: [
      [0, 0],
      [0, 1],
      [1, 0],
      [1, 1],
    ],
    targetSize: { width: 1, height: 1 },
    movingSize: { width: 1, height: 1 },
  };

  test("registerLayer", () => {
    registerLayer(layer, recipe);
    expect(layer.uniform.mRegister.value).toStrictEqual(matrix);
  });
});
