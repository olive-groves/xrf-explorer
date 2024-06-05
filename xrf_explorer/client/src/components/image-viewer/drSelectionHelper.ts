import {computed, inject, ref, watch} from "vue";
import {appState, datasource} from "@/lib/appState";
import {SelectionToolInfo} from "@/lib/selection";
import {Layer, LayerType, Point2D} from "@/components/image-viewer/types";
import {SelectionOption} from "@/components/functional/selection/selection_tool.ts";
import {FrontendConfig} from "@/lib/config.ts";
import {hexToRgb} from "@/lib/utils";
import {useFetch} from "@vueuse/core";
import {toast} from "vue-sonner";
import {PNG} from "pngjs";
import {createReadStream} from "fs";
import {createLayer, layerGroups} from "@/components/image-viewer/state.ts";
import {createDataTexture, disposeLayer, loadLayer, updateDataTexture} from "@/components/image-viewer/scene.ts";
import {DataTexture} from "three";
import {layerGroupDefaults} from "@/components/image-viewer/workspace.ts";

const selection = computed(() => appState.selection.drSelection);

const config: FrontendConfig = inject<FrontendConfig>("config")!;
const embeddingWidth: number = 2000;        // TODO: not sure how to get the width of the embedding
const embeddingHeight: number = 8000;       // TODO: not sure how to get the height of the base image
let imageWidth: number = -1;
let imageHeight: number = -1;
// each index represents a pixel and the value represents whether the pixel is selected
const bitmask: boolean[] = new Array<boolean>(embeddingWidth * embeddingHeight);
const middleImagePath = ref();
// buffer with color data for each pixel
const layerData: Uint8Array = new Uint8Array(imageWidth * imageHeight * 4);
const layerTexture: DataTexture = createDataTexture(layerData, imageWidth, imageHeight);

watch(selection, onSelectionUpdate, { immediate: true, deep: true });

async function onSelectionUpdate(newSelection: SelectionToolInfo) {

    updateBitmask(newSelection);
    await getMiddleImage();
    const middleImageToEmbedding: { imagePoint: Point2D, embeddingPoint: Point2D }[] = mapImageToEmbedding();
    const selectedPointsInImage: Point2D[] = middleImageToEmbedding
        .filter((mapping) => bitmask[coordinatesToIndex(mapping.embeddingPoint.x, mapping.embeddingPoint.y, embeddingWidth)])
        .map((mapping) => mapping.imagePoint);
    updateLayer(selectedPointsInImage);

}

function updateBitmask(newSelection: SelectionToolInfo) {
    for (let i = 0; i < bitmask.length; i++) {
        // compute coordinates of point `i`
        const point: Point2D = indexToCoordinates(i, embeddingWidth);

        switch (newSelection.selectionType) {
            case SelectionOption.Rectangle: {
                // bitmask[i] = true iff the pixel is inside the rectangle
                bitmask[i] =
                    newSelection.points[0].x <= point.x && point.x < newSelection.points[1].x &&
                    newSelection.points[0].y <= point.y && point.y < newSelection.points[1].y;
                break;
            }

            case SelectionOption.Lasso: {
                // bitmask[i] = true iff the pixel is inside the polygon
                bitmask[i] = isInPolygon(point, newSelection.points);
                break;
            }

            default: {
                console.error("Selection type", newSelection.selectionType, "not recognized");
                bitmask[i] = false;
            }
        }
    }
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
 
        if (point.y > Math.min(polyPoint1.y, polyPoint2.y))         // point.y is above the lowest point in the poly
            if (point.y <= Math.max(polyPoint1.y, polyPoint2.y))    // point.y is below the highest point in the poly
                if (point.x <= Math.max(polyPoint1.x, polyPoint2.x)) {
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

async function getMiddleImage() {
    const url: string = `${config.api.endpoint}/${datasource.value}/dr/embedding/mapping`;
    const { response, data } = useFetch(url).get().blob();

    // error handling
    if (!(response.value?.ok && data.value != null)) {
        console.error("Failed to fetch middle image from: ", url);
        toast.error("An error occurred while parsing the Dimensionality Reduction selection.");
        return;
    }

    // store the middle image path
    middleImagePath.value = URL.createObjectURL(data.value).toString();
    console.info("Loaded middle image for DR selection.");
}

/**
 * For each pixel in the middle image, map it to the corresponding pixel in the embedding if it exists in the embedding.
 * We use `pngjs` to get the middle image's pixels' RGB values: https://www.npmjs.com/package/pngjs
 */
function mapImageToEmbedding() {
    const map: { imagePoint: Point2D, embeddingPoint: Point2D }[] = [];
    createReadStream(middleImagePath.value).pipe(new PNG()).on("parsed", function() {
        // update image dimensions
        imageWidth = this.width;    // TODO: how do i fix this?
        imageHeight = this.height;

        for (let x: number = 0; x < imageWidth; x++)
            for (let y: number = 0; y < imageHeight; y++) {
                const pixelIndex: number = (coordinatesToIndex(x, y, imageWidth)) << 2;

                const red: number = this.data[pixelIndex];
                const green: number = this.data[pixelIndex + 1];
                const blue: number = this.data[pixelIndex + 2];

                // only pixels where blue = 255 are in the embedding
                if (blue == 255)
                    map.push({
                        imagePoint: { x: x, y: y },
                        embeddingPoint: { x: red, y: green }    // imageRed = embeddingX, imageGreen = embeddingY
                    });
            }
    });

    return map;
}


function updateLayer(selection: Point2D[]) {
    const selectionColor: [number, number, number] = hexToRgb("#FFEF00");   // shoutout to canary islands

    for (let i = 0; i < layerData.length; i++) {
        const pixelInSelection: boolean = selection.includes(indexToCoordinates(i, imageWidth));

        // if the pixel is in the selection, color it, otherwise make it transparent
        layerData[i] = pixelInSelection ? selectionColor[0] : 0;
        layerData[i + 1] = pixelInSelection ? selectionColor[1] : 0;
        layerData[i + 2] = pixelInSelection ? selectionColor[2] : 0;
        layerData[i + 3] = 255;   // opacity is set in the layer itself
    }

    if (layerGroups.value.selection != undefined) {
        const layer: Layer = layerGroups.value.selection.layers.filter(layer => layer.image == "dr_selection")[0];

        if (layer.mesh == undefined && selection.length > 0)        // layer was disposed of, load it again
            loadLayer(layer);
        else if (layer.mesh != undefined && selection.length == 0)  // layer was loaded, dispose of it
            disposeLayer(layer);

        updateDataTexture(layerGroups.value.selection);
    }
}

export async function createSelectionLayers() {
    const layers: Layer[] = [
        createLayer("selection_dr", "dr_selection", false),
        createLayer("selection_image_viewer", "image_viewer_selection", false),
    ]

    // set up layers
    layers.forEach(layer => {
        layer.uniform.iLayerType.value = LayerType.Selection;
        layer.uniform.tAuxiliary.value = { value: layerTexture, type: "t" };    // TODO: why do i get these errors?
    });

    // add layers to the groups of layers
    layerGroups.value.selection = {
        name: "Selections",
        description: "Visualizes the current selections",
        layers: layers,
        index: 5000,    // TODO: no sure which value to use here
        visible: true,
        ...layerGroupDefaults,
    }

    // set opacity to default values
    for (let i = 0; i < layerGroups.value.selection.layers.length; i++)
        layerGroups.value.selection.opacity[i] = config.selectionToolConfig.opacity;
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
