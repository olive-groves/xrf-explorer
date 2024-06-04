import { computed, watch } from "vue";
import { appState } from "@/lib/appState";
import { SelectionToolInfo } from "@/lib/selection";
import { Point2D } from "@/components/image-viewer/types";

const selection = computed(() => appState.selection.drSelection);

watch(selection, onSelectionUpdate, { immediate: true, deep: true });

function onSelectionUpdate(newSelection: SelectionToolInfo) {
    let selectedPixelsDr: Point2D[] = [];

    if (newSelection.selectionType == "Rectangle") {
        // get all the points inside the rectangle
        for (let x = newSelection.points[0].x; x < newSelection.points[1].x; x++)
            for (let y = newSelection.points[0].y; y < newSelection.points[1].y; y++)
                selectedPixelsDr.push({ x: x, y: y });
    }
}
