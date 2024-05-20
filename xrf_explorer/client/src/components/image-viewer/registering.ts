import { ContextualImage } from "@/lib/workspace";
import { Layer } from "./types";

/**
 * Sets the mRegister uniform on a layer in accordance with the specified recipe.
 * @param layer - The layer for which the perspective transform should be set.
 * @param _image - The image resource that will be used to request the correct recipe.
 */
export function registerLayer(layer: Layer, _image: ContextualImage) {
  layer.uniform.mRegister.value.set(1, 0, 0, 0, 1, 0, 0, 0, 1);
}
