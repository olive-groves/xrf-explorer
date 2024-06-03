import {Point2D} from "@/components/image-viewer/types";

/**
 * Type containing information relevant to the selection tool.
 */
export class SelectionTool {
    /**
     * Determines the type of selection the tool should perform (rectangle, lasso, etc.).
     */
    selectionType: SelectionOption;
    /**
     * The set of points which make up the selection. For rectangle selection these are the top-left and right-bottom
     * points, in that order.
     */
    selectedPoints: Point2D[] = [];
    /**
     * Determines whether the selection is currently being drawn.
     */
    activeSelection: boolean = false;
    /**
     * Determines whether the selection is currently complete.
     */
    finishedSelection: boolean = false;

    constructor() {
        this.selectionType = SelectionOption.Rectangle;
    }

    /**
     * Resets the necessary values to reflect an empty selection.
     */
    cancelSelection() {
        this.selectedPoints = [];
        this.activeSelection = false;
        this.finishedSelection = false;
    }

    /**
     * Add a given point to the list based on the chosen selection type and update the selection status accordingly. Will start a new selection if current selection is already complete.
     * @param newPoint - The point to be added to the list in Point2D format (the origin points (0, 0) must be at the top-left).
     */
    addPointToSelection(newPoint: Point2D) {

        // restart selection if the current selection is complete
        if (this.finishedSelection) {
            this.cancelSelection();
            console.log("Started new selection")
        }

        // we're adding a new point so regardless of the state the user is definitely actively editing the selection.
        this.activeSelection = true;
        // add the new point to the selection
        this.selectedPoints.push(newPoint);
        console.log("Added new point to selection at: ", newPoint.x, newPoint.y)

        switch (this.selectionType) {
            case SelectionOption.Lasso: {
                // TODO: add lasso selection
                break;
            }

            case SelectionOption.Rectangle: {
                this.handleRectangleSelection();
                break;
            }

            default: {
                console.log("Unrecognized selection type: " + this.selectionType);
                break;
            }
        }

        if (this.finishedSelection)
            console.log("Finished selection");

    }

    /**
     * Update the list of points based on a rectangle selection method and update the object's status accordingly.
     */
    handleRectangleSelection() {

        // TODO: origin in image viewer is bottom-left, but on image itself it's top-left, this needs to be converted when sending to the backend
        this.selectedPoints.sort((a, b) => a.y - b.y || a.x - b.x);

        // selection has concluded if we have 2 points
        this.activeSelection = this.selectedPoints.length != 2;
        this.finishedSelection = !this.activeSelection;

        // swap the points to ensure the list represents the top-left and bottom-right points
        if (this.finishedSelection) {
            this.selectedPoints = [{
                x: Math.min(this.selectedPoints[0].x, this.selectedPoints[1].x),
                y: Math.min(this.selectedPoints[0].y, this.selectedPoints[1].y)
            }, {
                x: Math.max(this.selectedPoints[0].x, this.selectedPoints[1].x),
                y: Math.max(this.selectedPoints[0].y, this.selectedPoints[1].y)
            }];
        }
    }

    getOrigin() {
        return this.selectedPoints[0];
    }

    getWidth() {
        return (this.selectionType == SelectionOption.Rectangle) ?
            Math.abs(this.selectedPoints[0].x - this.selectedPoints[1].x) : 0;
    }

    getHeight() {
        return (this.selectionType == SelectionOption.Rectangle) ?
            Math.abs(this.selectedPoints[0].y - this.selectedPoints[1].y) : 0;
    }

}

/**
 * Supported types of selection.
 */
export enum SelectionOption {
    Lasso = "lasso",
    Rectangle = "rectangle",
}
