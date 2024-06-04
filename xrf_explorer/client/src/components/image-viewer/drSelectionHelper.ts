import {computed, watch} from "vue";
import {appState} from "@/lib/appState";
import {SelectionToolInfo} from "@/lib/selection";
import {Point2D} from "@/components/image-viewer/types";
import {SelectionOption} from "@/components/functional/selection/selection_tool.ts";

const selection = computed(() => appState.selection.drSelection);

const embeddingWidth = 2000;        // TODO: not sure how to get the width of the embedding
const embeddingHeight = 8000;       // TODO: not sure how to get the height of the base image
// each index represents a pixel and the value represents whether the pixel is selected
const bitmask = new Array<boolean>(embeddingWidth * embeddingHeight);

watch(selection, onSelectionUpdate, { immediate: true, deep: true });

function onSelectionUpdate(newSelection: SelectionToolInfo) {

    updateBitmask(newSelection);

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
