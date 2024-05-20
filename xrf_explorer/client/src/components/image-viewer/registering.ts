import { Layer } from "./types";

/**
 *
 * @param layer
 * @param recipeLocation
 */
export function registerLayer(layer: Layer, recipeLocation: string) {
  layer.uniform.mRegister.value.set(1, 0, 0, 0, 1, 0, 0, 0, 1);
}
