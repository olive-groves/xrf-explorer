import { DataTexture } from "three";
import { computed, watch } from "vue";
import { toast } from "vue-sonner";
import { useFetch } from "@vueuse/core";
import { createDataTexture, disposeLayer, loadLayer, updateDataTexture } from "@/components/image-viewer/scene.ts";
import { createLayer, layerGroups, updateLayerGroupLayers } from "@/components/image-viewer/state.ts";
import { Layer, LayerType, Point2D } from "@/components/image-viewer/types";
import { layerGroupDefaults } from "@/components/image-viewer/workspace.ts";
import { appState, datasource } from "@/lib/appState";
import { DimensionalityReductionSelection, SelectionOption } from "@/lib/selection";
import { hexToRgb } from "@/lib/utils";
import { config } from "@/main";
import {getDataSize, getRecipe, getTargetSize} from "@/components/image-viewer/api.ts";
import {registerLayer} from "@/components/image-viewer/registering.ts";

const selection = computed(() => appState.selection.dimensionalityReduction);

// const config: FrontendConfig = inject<FrontendConfig>("config")!;
let embeddingWidth: number = -1;
let embeddingHeight: number = -1;
let imageWidth: number = -1;
let imageHeight: number = -1;
// list of pixels in the embedding scaled down to 256x256, pixels that are selected have a color, others have opacity 0
const layerData: Uint8Array = new Uint8Array(256 * 256 * 4);
const layerTexture: DataTexture = createDataTexture(layerData, imageWidth, imageHeight);

watch(selection, onSelectionUpdate, { immediate: true, deep: true });

async function onSelectionUpdate(newSelection: DimensionalityReductionSelection | null) {
    // ensure that the new selection is not undefined
    if (newSelection == null)
        return;

    // remove selection
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
    updateLayer(newSelection.points.length);
    console.info("Updated the image viewer to display the selection in the DR window.");

}

/**
 *
 * @param newSelection
 */
function updateBitmask(newSelection: DimensionalityReductionSelection): void {
    // the number of pixels in the embedding image
    const nPixels: number = embeddingWidth * embeddingHeight;

    // compute the indices of the bounding box in which the selection is contained for faster updates
    const boundingBox: Point2D[] = (newSelection.selectionType == SelectionOption.Rectangle) ?
        newSelection.points : getBoundingBox(newSelection);
    const topLeftIndex: number = coordinatesToIndex(boundingBox[0].x, boundingBox[0].y, embeddingWidth);
    const bottomRightIndex: number = coordinatesToIndex(boundingBox[1].x, boundingBox[1].y, embeddingWidth);

    // reset bitmask
    layerData.fill(0);

    // check which points are in the selection and update the bitmask accordingly
    for (let embeddingPixel: number = topLeftIndex; embeddingPixel <= bottomRightIndex; embeddingPixel++) {

        // index of the point in the 256x256 bitmask
        const normalizedIndex: number = Math.floor(embeddingPixel * 256 / nPixels);

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
        layerData[normalizedIndex + 3] = (isInSelection ? 255 : 0);     // opacity is set in the layer itself
    }
}

function getBoundingBox(selection: DimensionalityReductionSelection): Point2D[] {
    const xCoords: number[] = selection.points.map(point => point.x);
    const yCoords: number[] = selection.points.map(point => point.y);
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
 *
 * @param point
 * @param selection
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
 *
 * @param point
 * @param rectangleBoundingPoints
 */
function isInRectangle(point: Point2D, rectangleBoundingPoints: Point2D[]): boolean {
    return rectangleBoundingPoints[0].x <= point.x && point.x < rectangleBoundingPoints[1].x &&
        rectangleBoundingPoints[0].y <= point.y && point.y < rectangleBoundingPoints[1].y;
}

/**
 * Adapted from https://www.geeksforgeeks.org/how-to-check-if-a-given-point-lies-inside-a-polygon/ .
 * @param point
 * @param polygon
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
 *
 * @param nPointsSelected
 */
async function updateLayer(nPointsSelected: number) {
    if (layerGroups.value.selection != undefined) {
        const layer: Layer = layerGroups.value.selection.layers.filter(layer => layer.id == "selection_dr")[0];

        if (layer.mesh == undefined && nPointsSelected > 0)        // layer was disposed of, load it again
            loadLayer(layer);
        else if (layer.mesh != undefined && nPointsSelected == 0)  // layer was loaded, dispose of it
            disposeLayer(layer);

        updateDataTexture(layerGroups.value.selection);
    }
    console.log("selection layer: ", layerGroups.value.selection);
}

/**
 *
 */
export async function createSelectionLayer() {
    const recipe = await getRecipe(`${config.api.endpoint}/${datasource.value}/data/recipe`);
    recipe.movingSize = await getDataSize();
    recipe.targetSize = await getTargetSize();

    // set up layer
    const layers: Layer[] = [];
    const layer: Layer = createLayer("selection_dr",
        `${config.api.endpoint}/${datasource.value}/dr/embedding/mapping`, false)
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

    // set opacity to default values
    for (let i = 0; i < layerGroups.value.selection.layers.length; i++)
        layerGroups.value.selection.opacity[i] = config.selectionToolConfig.opacity;

    updateLayerGroupLayers(layerGroups.value.selection);
}

/**
 * Convert an index from a flattened matrix into a Point2D object.
 * @param index - Index in the array of the point to be obtained.
 * @param imageWidth - Width of the image on which the array is based.
 */
function indexToCoordinates(index: number, imageWidth: number) {
    return { x: index % imageWidth, y: Math.floor(index / imageWidth) };
}

/**
 * Convert a Point2D object into an index of a flattened matrix.
 * @param x - X component of the point to be converted.
 * @param y - Y component of the point to be converted.
 * @param imageWidth - Width of the image on which the array is based.
 */
function coordinatesToIndex(x: number, y: number, imageWidth: number) {
    return y * imageWidth + x;
}
