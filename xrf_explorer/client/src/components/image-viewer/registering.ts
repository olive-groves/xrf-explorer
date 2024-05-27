import { ContextualImage } from "@/lib/workspace";
import { Layer } from "./types";
import * as THREE from "three";
import * as math from "mathjs";

const recipes: {
  [key: string]: RegisteringRecipe;
} = {};

/**
 * Sets the mRegister uniform on a layer in accordance with the specified recipe.
 * @param layer - The layer for which the perspective transform should be set.
 * @param image - The image resource that will be used to request the correct recipe.
 */
export async function registerLayer(layer: Layer, image: ContextualImage) {
  if (image.recipeLocation == "") return;

  // Make sure that the recipe is known to the client.
  if (!(image.recipeLocation in recipes)) {
    const recipe = (await (await fetch(image.recipeLocation.replace(".csv", ".json"))).json()) as RegisteringRecipe;
    recipes[image.recipeLocation] = recipe;
  }

  const recipe = recipes[image.recipeLocation];
  setPerspectiveTransform(layer.uniform.mRegister.value, recipe);
}

/**
 * Sets a matrix to the perspective transform described by a registering recipe.
 * @param matrix - The matrix that should be set.
 * @param recipe - The recipe to use to calculate the transform.
 */
function setPerspectiveTransform(matrix: THREE.Matrix3, recipe: RegisteringRecipe) {
  const s = 2;
  const d = 2 - s;

  const points = recipe.points;

  // Unscale the points of the src image
  const scale = Math.min(
    recipe.targetSize.width / recipe.movingSize.width,
    recipe.targetSize.height / recipe.movingSize.height,
  );
  points.forEach((point) => {
    (point[s] = point[s] / scale), (point[s + 1] = point[s + 1] / scale);
  });

  // Matrices for Ax=B
  const A: number[][] = []; // 8 x 8
  const B = []; // 8 x 1
  for (let i = 0; i < 4; i++) {
    A.push([
      points[i][s],
      points[i][s + 1],
      1,
      0,
      0,
      0,
      -points[i][s] * points[i][d],
      -points[i][s + 1] * points[i][d],
    ]);
    B.push(points[i][d]);
  }
  for (let i = 0; i < 4; i++) {
    A.push([
      0,
      0,
      0,
      points[i][s],
      points[i][s + 1],
      1,
      -points[i][s] * points[i][d + 1],
      -points[i][s + 1] * points[i][d + 1],
    ]);
    B.push(points[i][d + 1]);
  }

  // Solve Ax = B and extract solution
  const x = math.lusolve(A, B) as number[][]; // 8 x 1

  matrix.set(x[0][0], x[1][0], x[2][0], x[3][0], x[4][0], x[5][0], x[6][0], x[7][0], 1);
  console.log("Set transform", recipe, matrix);
}

/**
 * Type describing a registering recipe.
 */
export type RegisteringRecipe = {
  /**
   * The size of the target image, always the base image.
   */
  targetSize: {
    width: number;
    height: number;
  };
  /**
   * The size of the moving image, the image that needs to be registered.
   */
  movingSize: {
    width: number;
    height: number;
  };
  /**
   * The four sets of points describing the perspective transform.
   */
  points: [RegisteringRecipePoint, RegisteringRecipePoint, RegisteringRecipePoint, RegisteringRecipePoint];
};

/**
 * A set of values describing the translation of a point.
 * In the format targetX, targetY, movingX, movingY.
 */
export type RegisteringRecipePoint = [number, number, number, number];
