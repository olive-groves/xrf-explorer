import { DataTexture } from "three";
import { computed, watch } from "vue";
import { toast } from "vue-sonner";
import { getDataSize, getRecipe, getTargetSize } from "@/components/image-viewer/api";
import { registerLayer } from "@/components/image-viewer/registering";
import { createDataTexture, disposeLayer, loadLayer, updateDataTexture } from "@/components/image-viewer/scene";
import { createLayer, layerGroups, updateLayerGroupLayers } from "@/components/image-viewer/state";
import { Layer, LayerType } from "@/components/image-viewer/types";
import { layerGroupDefaults } from "@/components/image-viewer/workspace";
import { appState, datasource } from "@/lib/appState";
import { DimensionalityReductionSelection, SelectionOption } from "@/lib/selection";
import { hexToRgb, Point2D } from "@/lib/utils";
import { config } from "@/main";

const selection = computed(() => appState.selection.dimensionalityReduction);

const width: number = 256; // arbitrary amount to compress embedding data
const height: number = 256; // arbitrary amount to compress embedding data
// list of pixels in the embedding scaled down to 256x256, pixels that are selected have a color, others have opacity 0
const data: Uint8Array = new Uint8Array(width * height * 4);
const dataTexture: DataTexture = createDataTexture(data, width, height);

watch(selection, onSelectionUpdate, { immediate: true, deep: true });

/**
 * Set the color of the selection layer.
 * @param color - Color to be used for highlighting the selection.
 */
function setSelectionColor(color: [number, number, number]): void {
  color.push(0); // opacity set to 0 (used for bitmask)
  for (let i: number = 0; i < data.length; i++) data[i] = color[i % 4];
}

/**
 * Perform any and all necessary updates to the DR Selection layer when a new selection comes through.
 * @param newSelection - Object containing all necessary information about the selection to update the layer.
 */
async function onSelectionUpdate(newSelection: DimensionalityReductionSelection | null) {
  // ensure that the new selection is not undefined
  if (newSelection == null) return;

  // remove current selection
  if (newSelection.points.length == 0) {
    updateLayer(0);
    console.info("Removed dimensionality reduction selection.");
    return;
  }

  // edge case: rectangle selection must have exactly 2 points
  if (newSelection.selectionType == SelectionOption.Rectangle && newSelection.points.length != 2) {
    console.error("Invalid rectangle selection. Expected 2 points but got: ", newSelection);
    return;
  }
  // edge case: polygon selection must have at least 3 points
  if (newSelection.selectionType == SelectionOption.Lasso && newSelection.points.length < 3) {
    console.error("Invalid polygon selection. Expected at least 3 points but got: ", newSelection);
    return;
  }

  updateBitmask(newSelection);

  // update the layer to display the selection
  updateLayer(newSelection.points.length);
  toast.info("Now displaying the dimensionality reduction selection.");
  console.info("Updated the image viewer to display the selection in the DR window.");
}

/**
 * Update the bitmask of the embedding image to denote which pixels are in the new selection.
 * @param newSelection - Object containing all necessary information about the selection to update the layer.
 */
function updateBitmask(newSelection: DimensionalityReductionSelection): void {
  // compute the indices of the bounding box in which the selection is contained for faster updates
  const boundingBox: Point2D[] =
    newSelection.selectionType == SelectionOption.Rectangle ? newSelection.points : getBoundingBox(newSelection.points);
  const topLeftPoint: Point2D = boundingBox[0];
  const bottomRightPoint: Point2D = boundingBox[1];

  // reset bitmask (through the opacity)
  for (let i: number = 3; i < data.length; i += 4) data[i] = 0;

  // check which points are in the selection and update the bitmask accordingly
  for (let x: number = topLeftPoint.x; x <= bottomRightPoint.x; x++) {
    for (let y: number = topLeftPoint.y; y <= bottomRightPoint.y; y++) {
      // the middle image's coordinate system has its origin at the bottom left, embedding has it at the top left
      const point: Point2D = { x: x, y: y };
      // point with correct origin
      const convertedPoint: Point2D = { x: point.x, y: height - point.y };
      // index in the 256x256 image version of the embedding with the correct coordinate system
      const convertedIndex: number = coordinatesToIndex(convertedPoint.x, convertedPoint.y, width);
      // index of the point in the 256x256x4 bitmask
      const normalizedIndex: number = Math.floor(convertedIndex * 4);

      // we don't want to overwrite the selection
      if (data[normalizedIndex + 3] != 0) continue;

      const isInSelection: boolean = isPointInSelection(point, newSelection);

      // update the layer's bitmask
      // opacity is 0 if the point is not in the selection, otherwise the opacity is set to the config default
      data[normalizedIndex + 3] = isInSelection ? 255 : 0;
    }
  }
}

/**
 * Compute the smallest rectangle encapsulating every point in a polygon.
 * @param delimitingPoints - List of points that make up the polygon (vertices).
 * @returns The top-left and bottom-right points of the computed bounding box, in that order.
 */
function getBoundingBox(delimitingPoints: Point2D[]): Point2D[] {
  const xCoords: number[] = delimitingPoints.map((point: Point2D) => point.x);
  const yCoords: number[] = delimitingPoints.map((point: Point2D) => point.y);
  return [
    {
      x: Math.min(...xCoords),
      y: Math.min(...yCoords),
    },
    {
      x: Math.max(...xCoords),
      y: Math.max(...yCoords),
    },
  ];
}

/**
 * Compute whether a given point lies in a given selection.
 * @param point - The point to check.
 * @param selection - Object containing all necessary information about the selection to check against.
 * @returns True if the point lies in the selection, false otherwise.
 */
function isPointInSelection(point: Point2D, selection: DimensionalityReductionSelection): boolean {
  switch (selection.selectionType) {
    case SelectionOption.Rectangle:
      return isInRectangle(point, selection.points);

    case SelectionOption.Lasso:
      return isInPolygon(point, selection.points);

    default: {
      console.error("Selection type", selection.selectionType, "not recognized");
      return false;
    }
  }
}

/**
 * Compute whether a given point lies in a given rectangle.
 * @param point - The point to check.
 * @param rectangleBoundingPoints - The top-left and bottom-right points of the rectangle to check against.
 * @returns True if the point lies in the rectangle, false otherwise.
 */
function isInRectangle(point: Point2D, rectangleBoundingPoints: Point2D[]): boolean {
  return (
    rectangleBoundingPoints[0].x <= point.x &&
    point.x < rectangleBoundingPoints[1].x &&
    rectangleBoundingPoints[0].y <= point.y &&
    point.y < rectangleBoundingPoints[1].y
  );
}

/**
 * Compute whether a given point lies in a given polygon.
 * Adapted from https://www.geeksforgeeks.org/how-to-check-if-a-given-point-lies-inside-a-polygon/ .
 * @param point - The point to check.
 * @param polygon - The list of points that make up the polygon to check against.
 * @returns True if the point lies in the polygon, false otherwise.
 */
function isInPolygon(point: Point2D, polygon: Point2D[]): boolean {
  let inside: boolean = false;

  let polyPoint1: Point2D = polygon[0];
  let polyPoint2: Point2D;

  // iterate through all edges in the polygon, starting at the second and finishing at the first
  for (let i = 1; i <= polygon.length; i++) {
    polyPoint2 = polygon[i % polygon.length]; // last i = polygon.length, we need i = 0 in this case

    if (
      point.y > Math.min(polyPoint1.y, polyPoint2.y) && // point.y is above the lowest point in the poly
      point.y <= Math.max(polyPoint1.y, polyPoint2.y) && // point.y is below the highest point in the poly
      point.x <= Math.max(polyPoint1.x, polyPoint2.x)
    ) {
      const x_intersection: number =
        ((point.y - polyPoint1.y) * (polyPoint2.x - polyPoint1.x)) / (polyPoint2.y - polyPoint1.y) + polyPoint1.x;

      if (polyPoint1.x == polyPoint2.x || point.x <= x_intersection) inside = !inside;
    }

    polyPoint1 = polyPoint2; // advance polyPoint1 by 1 edge in the polygon list
  }

  return inside;
}

/**
 * Find the DR Selection layer and update its data based on the new selection.
 * @param nPointsSelected - Number of points in the new selection.
 */
function updateLayer(nPointsSelected: number): void {
  if (layerGroups.value.selection != undefined) {
    const layer: Layer = getDRSelectionLayer();
    const isLoaded: boolean = layer.mesh != undefined; // true if the layer is currently loaded

    if (!isLoaded && nPointsSelected > 0)
      // layer was not loaded, load it again
      loadLayer(layer, false);
    else if (!isLoaded && nPointsSelected == 0)
      // layer was loaded, remove it
      disposeLayer(layer);

    updateDataTexture(layerGroups.value.selection);
  }
}

/**
 * Find and return the DR selection layer from the layer groups.
 * @returns The layer corresponding to the DR selection.
 */
function getDRSelectionLayer(): Layer {
  return layerGroups.value.selection.layers.filter((layer: Layer): boolean => layer.id == "selection_dr")[0];
}

/**
 * Update the middle image by reloading the layer.
 */
export function updateMiddleImage(): void {
  const layer: Layer = getDRSelectionLayer();
  const isLoaded: boolean = layer.mesh != undefined; // define current state of the layer

  if (isLoaded) disposeLayer(layer); // remove the layer so we can update it
  loadLayer(layer, false); // update the middle image
  if (!isLoaded) disposeLayer(layer); // reset to previous state
}

/**
 * Create the first instance of the DR Selection layer and add it to the global group of layers.
 */
export async function createDRSelectionLayer() {
  setSelectionColor(hexToRgb(config.selectionTool.fill_color));

  const recipe = await getRecipe(`${config.api.endpoint}/${datasource.value}/data/recipe`);
  recipe.movingSize = await getDataSize();
  recipe.targetSize = await getTargetSize();

  // set up layer
  const layer: Layer = createLayer(
    "selection_dr",
    `${config.api.endpoint}/${datasource.value}/dr/embedding/mapping`,
    false,
  );
  registerLayer(layer, recipe);
  layer.uniform.iLayerType.value = LayerType.DimensionalityReductionSelection;
  layer.uniform.tAuxiliary = { value: dataTexture, type: "t" };

  // add layers to the groups of layers
  layerGroups.value.selection = {
    name: "Dimensionality reduction",
    description: "Selection visualization",
    layers: [layer],
    index: -2,
    visible: true,
    ...layerGroupDefaults,
  };

  updateLayerGroupLayers(layerGroups.value.selection);
}

/**
 * Convert a Point2D object into an index of a flattened matrix.
 * @param x - X component of the point to be converted.
 * @param y - Y component of the point to be converted.
 * @param imageWidth - Width of the image on which the array is based.
 * @returns Index in the array of the point at the given coordinates.
 */
function coordinatesToIndex(x: number, y: number, imageWidth: number) {
  return Math.floor(y * imageWidth + x);
}
