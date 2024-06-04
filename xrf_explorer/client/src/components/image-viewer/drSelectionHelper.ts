import {computed, inject, ref, watch} from "vue";
import {appState, datasource} from "@/lib/appState";
import {SelectionToolInfo} from "@/lib/selection";
import {Point2D} from "@/components/image-viewer/types";
import {SelectionOption} from "@/components/functional/selection/selection_tool.ts";
import {FrontendConfig} from "@/lib/config.ts";
import {useFetch} from "@vueuse/core";
import {toast} from "vue-sonner";
import { PNG } from "pngjs";
import { createReadStream } from "fs";

const selection = computed(() => appState.selection.drSelection);

const config = inject<FrontendConfig>("config")!;
const embeddingWidth = 2000;        // TODO: not sure how to get the width of the embedding
const embeddingHeight = 8000;       // TODO: not sure how to get the height of the base image
// each index represents a pixel and the value represents whether the pixel is selected
const bitmask = new Array<boolean>(embeddingWidth * embeddingHeight);
const middleImagePath = ref();

watch(selection, onSelectionUpdate, { immediate: true, deep: true });

async function onSelectionUpdate(newSelection: SelectionToolInfo) {

    updateBitmask(newSelection);
    await getMiddleImage();
    const middleImageToEmbedding: { imagePoint: Point2D, embeddingPoint: Point2D }[] = mapImageToEmbedding();

}

function updateBitmask(newSelection: SelectionToolInfo) {
    for (let i = 0; i < bitmask.length; i++) {
        // compute coordinates of point `i`
        const x = i % embeddingWidth;
        const y = Math.floor(i / embeddingWidth);

        switch (newSelection.selectionType) {
            case SelectionOption.Rectangle: {
                // bitmask[i] = true iff the pixel is inside the rectangle
                bitmask[i] =
                    newSelection.points[0].x <= x && x < newSelection.points[1].x &&
                    newSelection.points[0].y <= y && y < newSelection.points[1].y;
                break;
            }

            case SelectionOption.Lasso: {
                // bitmask[i] = true iff the pixel is inside the polygon
                bitmask[i] = isInPolygon({x, y}, newSelection.points);
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
        for (let x: number = 0; x < this.width; x++)
            for (let y: number = 0; y < this.height; y++) {
                const pixelIndex: number = (this.width * y + x) << 2;

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
