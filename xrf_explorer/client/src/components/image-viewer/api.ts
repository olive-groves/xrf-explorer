import { appState, datasource } from "@/lib/appState";
import { config } from "@/main";
import { RegisteringRecipe } from "./registering";
import { h, markRaw } from "vue";
import { toast } from "vue-sonner";

/**
 * Represents a 2 dimensional size.
 */
export type Size = {
  /**
   * The width of the target image.
   */
  width: number;
  /**
   * The height of the target image.
   */
  height: number;
};

const sizeCache: { [key: string]: Size } = {};

/**
 * Gets the size of the base/target image.
 * @returns The size of the base/target image in pixels.
 */
export async function getTargetSize(): Promise<Size> {
  return getImageSize(appState.workspace!.baseImage.name);
}

/**
 * Gets the size of a 2D object from a URL.
 * @param url - The url to the 2D object.
 * @returns The size of the 2D object in pixels.
 */
async function extract2DSize(url: string): Promise<Size> {
  if (!(url in sizeCache)) {
    sizeCache[url] = (await (await fetch(url)).json()) as Size;
  }
  const size: Size = sizeCache[url];
  size.width = parseInt(size.width as unknown as string);
  size.height = parseInt(size.height as unknown as string);
  return size;
}

/**
 * Gets the size of a specific image, mainly used for registering.
 * @param name - The name of the contextual image to get the size of.
 * @returns The size of the specified image in pixels.
 */
export async function getImageSize(name: string): Promise<Size> {
  const url: string = `${config.api.endpoint}/${datasource.value}/image/${name}/size`;
  return await extract2DSize(url);
}

/**
 * Gets the size of the generated data images, based on the size of the data cubes.
 * @returns The size of the data cubes.
 */
export async function getDataSize(): Promise<Size> {
  const url: string = `${config.api.endpoint}/${datasource.value}/data/size`;
  return await extract2DSize(url);
}

/**
 * Gathers all details required to create a RegisteringRecipe.
 * @param recipeLocation - The url to the registering recipe.
 * @returns The registering recipe. MovingSize and targetSize will be left undefined and should be set manually.
 */
export async function getRecipe(recipeLocation: string): Promise<RegisteringRecipe> {
  try {
    return (await (await fetch(recipeLocation)).json()) as RegisteringRecipe;
  } catch {}

  console.warn(`Failed to gather registering recipe from ${recipeLocation}`);
  toast.warning("Failed to gather registering recipe", {
    description: markRaw(h("div", ["Request to ", h("code", recipeLocation), " failed"])),
  });

  // In case of error, return a recipe that will not alter the layer.
  return {
    moving: [
      [0, 0],
      [0, 1],
      [1, 1],
      [1, 0],
    ],
    target: [
      [0, 0],
      [0, 1],
      [1, 1],
      [1, 0],
    ],
  };
}
