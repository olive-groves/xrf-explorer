import { DataTexture } from "three";
import { computed, watch } from "vue";
import { createDataTexture, disposeLayer, loadLayer, updateDataTexture } from "@/components/image-viewer/scene";
import { createLayer, layerGroups, updateLayerGroupLayers } from "@/components/image-viewer/state";
import { Layer, LayerType, Point2D } from "@/components/image-viewer/types";
import { layerGroupDefaults } from "@/components/image-viewer/workspace";
import { appState, datasource } from "@/lib/appState";
import { DimensionalityReductionSelection, SelectionOption } from "@/lib/selection";
import { hexToRgb } from "@/lib/utils";
import { config } from "@/main";
import { getDataSize, getRecipe, getTargetSize } from "@/components/image-viewer/api";
import { registerLayer } from "@/components/image-viewer/registering";

const selection = computed(() => appState.selection.dimensionalityReduction);

let embeddingWidth: number = -1;
let embeddingHeight: number = -1;
const width: number = 256;          // arbitrary amount to compress embedding data
const height: number = 256;         // arbitrary amount to compress embedding data
const middleImageApiUrl: string = `${config.api.endpoint}/${datasource.value}/dr/embedding/mapping`;
// list of pixels in the embedding scaled down to 256x256, pixels that are selected have a color, others have opacity 0
const layerData: Uint8Array = new Uint8Array(width * height * 4);
const layerTexture: DataTexture = createDataTexture(layerData, width, height);

watch(selection, onSelectionUpdate, { immediate: true, deep: true });

/**
 * Perform any and all necessary updates to the DR Selection layer when a new selection comes through.
 * @param newSelection - Object containing all necessary information about the selection to update the layer.
 */
async function onSelectionUpdate(newSelection: DimensionalityReductionSelection | null) {
    // ensure that the new selection is not undefined
    if (newSelection == null)
        return;

    // remove selection
    if (newSelection.points.length == 0) {
        updateLayer(0, false);
        console.info("Removed dimensionality reduction selection.");
        return;
    }

    // edge case: rectangle selection must have exactly 2 points
    if (newSelection.selectionType == SelectionOption.Rectangle && newSelection.points.length != 2) {
        console.error("Invalid rectangle selection. Expected 2 points but got: ", newSelection);
        return;
    }
    // edge case: polygon selection must have at least 2 points
    if (newSelection.selectionType == SelectionOption.Lasso && newSelection.points.length < 2) {
        console.error("Invalid polygon selection. Expected at least 2 points but got: ", newSelection);
        return;
    }

    // extract selection information
    let { width, height } = newSelection.embeddedImageDimensions;
    embeddingWidth = width;
    embeddingHeight = height;
    updateBitmask(newSelection);

    // update the layer to display the selection
    updateLayer(newSelection.points.length, newSelection.updateMiddleImage);
    console.info("Updated the image viewer to display the selection in the DR window.");

}

/**
 * Update the bitmask of the embedding image to denote which pixels are in the new selection.
 * @param newSelection - Object containing all necessary information about the selection to update the layer.
 */
function updateBitmask(newSelection: DimensionalityReductionSelection): void {
    // the number of pixels in the embedding image
    const nPixels: number = embeddingWidth * embeddingHeight;

    // compute the indices of the bounding box in which the selection is contained for faster updates
    const boundingBox: Point2D[] = (newSelection.selectionType == SelectionOption.Rectangle) ?
        newSelection.points : getBoundingBox(newSelection.points);
    const topLeftIndex: number = coordinatesToIndex(boundingBox[0].x, boundingBox[0].y, embeddingWidth);
    const bottomRightIndex: number = coordinatesToIndex(boundingBox[1].x, boundingBox[1].y, embeddingWidth);

    // reset bitmask
    layerData.fill(0);

    // check which points are in the selection and update the bitmask accordingly
    for (let embeddingPixel: number = topLeftIndex; embeddingPixel <= bottomRightIndex; embeddingPixel++) {

        // the middle image's coordinate system has its origin at the bottom left, embedding has it at the top left
        const pointCoords: Point2D = indexToCoordinates(embeddingPixel, embeddingWidth);
        const convertedPoint: Point2D = { x:  pointCoords.x, y: embeddingHeight - pointCoords.y };
        const convertedIndex: number = coordinatesToIndex(convertedPoint.x, convertedPoint.y, width);

        // index of the point in the 256x256 bitmask
        const normalizedIndex: number = Math.floor(convertedIndex * 256 / nPixels);

        // we don't want to overwrite the selection
        if (layerData[normalizedIndex] != 0 &&
            layerData[normalizedIndex + 1] != 0 &&
            layerData[normalizedIndex + 2] != 0)
            continue;

        // compute coordinates of point `i`
        const point: Point2D = indexToCoordinates(embeddingPixel, embeddingWidth);
        const isInSelection: boolean = isPointInSelection(point, newSelection);

        // update the layer's bitmask
        const selectionColor: [number, number, number] = hexToRgb("#FFEF00");   // shoutout to canary islands
        for (let rgbValue = 0; rgbValue < 3; rgbValue++)        // rgbValue corresponds to red, green, blue
            layerData[normalizedIndex + rgbValue] = (isInSelection ? selectionColor[rgbValue] : 0);
        // opacity is 0 if the point is not in the selection, otherwise the opacity is set to the config default
        layerData[normalizedIndex + 3] = (isInSelection ? config.selectionToolConfig.opacity : 0);
    }
}

/**
 * Compute the smallest rectangle encapsulating every point in a polygon.
 * @param delimitingPoints - List of points that make up the polygon (vertices)
 * @returns The top-left and bottom-right points of the computed bounding box, in that order.
 */
function getBoundingBox(delimitingPoints: Point2D[]): Point2D[] {
    const xCoords: number[] = delimitingPoints.map(point => point.x);
    const yCoords: number[] = delimitingPoints.map(point => point.y);
    return [
        {
            x: Math.min(...xCoords),
            y: Math.min(...yCoords)
        },
        {
            x: Math.max(...xCoords),
            y: Math.max(...yCoords)
        }
    ]
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
    return rectangleBoundingPoints[0].x <= point.x && point.x < rectangleBoundingPoints[1].x &&
        rectangleBoundingPoints[0].y <= point.y && point.y < rectangleBoundingPoints[1].y;
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
        polyPoint2 = polygon[i % polygon.length];   // last i = polygon.length, we need i = 0 in this case

        if ((point.y > Math.min(polyPoint1.y, polyPoint2.y)) &&     // point.y is above the lowest point in the poly
             (point.y <= Math.max(polyPoint1.y, polyPoint2.y)) &&   // point.y is below the highest point in the poly
                (point.x <= Math.max(polyPoint1.x, polyPoint2.x))) {
                    const x_intersection: number =
                        ((point.y - polyPoint1.y) * (polyPoint2.x - polyPoint1.x)) / (polyPoint2.y - polyPoint1.y) +
                        polyPoint1.x;

                    if (polyPoint1.x == polyPoint2.x || point.x <= x_intersection)
                        inside = !inside;
                }

        polyPoint1 = polyPoint2;    // advance polyPoint1 by 1 edge in the polygon list
    }

    return inside;
}

/**
 * Find the DR Selection layer and update its data based on the new selection.
 * @param nPointsSelected - Number of points in the new selection.
 * @param updateImage - True if the middle image needs to be updated, false otherwise.
 */
function updateLayer(nPointsSelected: number, updateImage: boolean): void {
    if (layerGroups.value.selection != undefined) {
        const layer: Layer = layerGroups.value.selection.layers.filter(layer => layer.id == "selection_dr")[0];

        const isLoaded: boolean = layer.mesh != undefined;  // true if the layer is currently loaded

        // reload the middle image if necessary
        if (updateImage) {
            if (isLoaded) disposeLayer(layer);      // remove the layer so we can update it
            loadLayer(layer);                       // update the middle image
            if (!isLoaded) disposeLayer(layer);     // reset to previous state
        }

        if (!isLoaded && nPointsSelected > 0)       // layer was not loaded, load it again
            loadLayer(layer);
        else if (!isLoaded && nPointsSelected == 0) // layer was loaded, remove it
            disposeLayer(layer);

        updateDataTexture(layerGroups.value.selection);
    }
}

/**
 * Create the first instance of the DR Selection layer and add it to the global group of layers.
 */
export async function createDRSelectionLayer() {
    const recipe = await getRecipe(`${config.api.endpoint}/${datasource.value}/data/recipe`);
    recipe.movingSize = await getDataSize();
    recipe.targetSize = await getTargetSize();

    // set up layer
    const layers: Layer[] = [];
    const layer: Layer = createLayer("selection_dr", middleImageApiUrl, false);
    registerLayer(layer, recipe);
    layer.uniform.iLayerType.value = LayerType.Selection;
    layer.uniform.tAuxiliary = { value: layerTexture, type: "t" };

    // add layers to the groups of layers
    layerGroups.value.selection = {
        name: "DR Selection",
        description: "Visualizes the current selection in the DR Window",
        layers: layers,
        index: -2,
        visible: true,
        ...layerGroupDefaults,
    }

    updateLayerGroupLayers(layerGroups.value.selection);
}

/**
 * Convert an index from a flattened matrix into a Point2D object.
 * @param index - Index in the array of the point to be obtained.
 * @param imageWidth - Width of the image on which the array is based.
 * @returns Point2D object containing the coordinates of the point at the given index.
 */
function indexToCoordinates(index: number, imageWidth: number) {
    return { x: index % imageWidth, y: Math.floor(index / imageWidth) };
}

/**
 * Convert a Point2D object into an index of a flattened matrix.
 * @param x - X component of the point to be converted.
 * @param y - Y component of the point to be converted.
 * @param imageWidth - Width of the image on which the array is based.
 * @returns Index in the array of the point at the given coordinates.
 */
function coordinatesToIndex(x: number, y: number, imageWidth: number) {
    return y * imageWidth + x;
}
