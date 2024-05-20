import { ContextualImage } from "@/lib/workspace";
import { Layer, Point2D } from "./types";
import math from "mathjs";
import * as THREE from "three";

/**
 * Sets the mRegister uniform on a layer in accordance with the specified recipe.
 * @param layer - The layer for which the perspective transform should be set.
 * @param _image - The image resource that will be used to request the correct recipe.
 */
export function registerLayer(layer: Layer, _image: ContextualImage) {
  layer.uniform.mRegister.value.set(1, 0, 0, 0, 1, 0, 0, 0, 1);
}

/**
 * Changes a provided matrix to contain the perspective transform generated from a registering recipe.
 * @param mat - A matrix that will contain the perspective transform.
 * @param src - An array of 4 points representing the source quadrilateral's corners.
 * @param dst - An array of 4 points representing the destination quadrilateral's corners.
 * @param srcWidth - Width of source image.
 * @param srcHeight - Height of source image.
 * @param dstWidth - Width of destination image.
 * @param dstHeight - Height of destination image.
 */
function _setPerspectiveTransform(
  mat: THREE.Matrix3,
  src: Point2D[],
  dst: Point2D[],
  srcWidth: number,
  srcHeight: number,
  dstWidth: number,
  dstHeight: number,
) {
  // Unscale the points of the src image
  const scale = Math.min(dstWidth / srcWidth, dstHeight / srcHeight);
  src.forEach((point) => {
    (point.x = point.x / scale), (point.y = point.y / scale);
  });

  // Matrices for Ax=B
  const A = []; // 8 x 8
  const B = []; // 8 x 1
  for (let i = 0; i < 4; i++) {
    A.push([src[i].x, src[i].y, 1, 0, 0, 0, -src[i].x * dst[i].x, -src[i].y * dst[i].x]);
    B.push(dst[i].x);
  }
  for (let i = 0; i < 4; i++) {
    A.push([0, 0, 0, src[i].x, src[i].y, 1, -src[i].x * dst[i].y, -src[i].y * dst[i].y]);
    B.push(dst[i].y);
  }

  // Solve Ax = B and extract solution
  const x = math.lusolve(A, B) as number[][]; // 8 x 1

  mat.set(x[0][0], x[1][0], x[2][0], x[3][0], x[4][0], x[5][0], x[6][0], x[7][0], 1);
}
