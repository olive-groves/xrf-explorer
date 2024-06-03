import { Layer } from "./types";
import * as THREE from "three";
import * as math from "mathjs";
import { deepClone } from "@/lib/utils";

const recipePromises: {
  [key: string]: Promise<RegisteringRecipe>;
} = {};

const recipes: {
  [key: string]: RegisteringRecipe;
} = {};

/**
 * Sets the mRegister uniform on a layer in accordance with the specified recipe.
 * @param layer - The layer for which the perspective transform should be set.
 * @param recipeLocation - The url to the registering recipe.
 */
export async function registerLayer(layer: Layer, recipeLocation: string) {
  if (recipeLocation == "") return;

  // Make sure that the recipe is known to the client.
  if (!(recipeLocation in recipes)) {
    // Start fetching the recipe if it has not been started already.
    if (!(recipeLocation in recipePromises)) {
      recipePromises[recipeLocation] = fetch(recipeLocation.replace(".csv", ".json")).then((response) =>
        response.json(),
      );
    }

    // Await the fetch completing.
    const recipe = (await recipePromises[recipeLocation]) as RegisteringRecipe;

    recipes[recipeLocation] = recipe;
  }

  const recipe = recipes[recipeLocation];
  setPerspectiveTransform(layer.uniform.mRegister.value, recipe);
}

/**
 * Sets a matrix to the perspective transform described by a registering recipe.
 * @param matrix - The matrix that should be set.
 * @param recipe - The recipe to use to calculate the transform.
 */
function setPerspectiveTransform(matrix: THREE.Matrix3, recipe: RegisteringRecipe) {
  const points = deepClone(recipe.points);
  const target = recipe.targetSize;
  const moving = recipe.movingSize;

  // Flip the y-coordinates
  // In the recipe y=0 is the top, in the image viewer y=0 is the bottom
  points.forEach((point) => {
    point[1] = target.height - point[1];
    point[3] = target.height - point[3];
  });

  // Compute the scaling applied to the image.
  const scaleW = target.width / moving.width;
  const scaleH = target.height / moving.height;
  const scale = Math.min(scaleW, scaleH);

  // Compensate for padding in the y-direction
  if (scaleH > scaleW) {
    const padding = target.height - scaleW * moving.height;
    points.forEach((point) => {
      point[3] -= padding;
    });
  }

  // Unscale the points of the src image
  points.forEach((point) => {
    (point[2] = point[2] / scale), (point[3] = point[3] / scale);
  });

  // Matrices for Ax=B
  const A: number[][] = []; // 8 x 8
  const B = []; // 8 x 1
  for (let i = 0; i < 4; i++) {
    A.push([points[i][2], points[i][3], 1, 0, 0, 0, -points[i][2] * points[i][0], -points[i][3] * points[i][0]]);
    B.push(points[i][0]);
  }
  for (let i = 0; i < 4; i++) {
    A.push([0, 0, 0, points[i][2], points[i][3], 1, -points[i][2] * points[i][1], -points[i][3] * points[i][1]]);
    B.push(points[i][1]);
  }

  // Solve Ax = B and extract solution
  const x = math.lusolve(A, B) as number[][]; // 8 x 1

  matrix.set(x[0][0], x[1][0], x[2][0], x[3][0], x[4][0], x[5][0], x[6][0], x[7][0], 1);
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
