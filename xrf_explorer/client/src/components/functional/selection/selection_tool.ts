import {Point2D} from "@/components/image-viewer/types";
import {FrontendConfig} from "@/lib/config.ts";
import * as d3 from "d3";

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

    constructor(selectionType: SelectionOption = SelectionOption.Rectangle) {
        this.selectionType = selectionType;
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
     * Set the necessary values to mark the selection as complete.
     */
    confirmSelection() {
        this.activeSelection = false;
        this.finishedSelection = true;
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
                this.handleLassoSelection();
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
     * Update the list of points to achieve a list of format `[top-left, bottom-right]`.
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

    /**
     * Update the list of points to avoid colliding areas.
     */
    handleLassoSelection() {
        // TODO: i have no clue how to actually do this
    }

    /**
     * Get the first point in the list.
     * @returns The first point in the list.
     */
    getOrigin() {
        return this.selectedPoints[0];
    }

    /**
     * Get the width of the selection (Rectangle selection only).
     * @returns The width of the selection for Rectangle selection, 0 otherwise.
     */
    getWidth() {
        return (this.selectionType == SelectionOption.Rectangle && this.selectedPoints.length == 2) ?
            Math.abs(this.selectedPoints[0].x - this.selectedPoints[1].x) : 0;
    }

    /**
     * Get the height of the selection (Rectangle selection only).
     * @returns The height of the selection for Rectangle selection, 0 otherwise.
     */
    getHeight() {
        return (this.selectionType == SelectionOption.Rectangle && this.selectedPoints.length == 2) ?
            Math.abs(this.selectedPoints[0].y - this.selectedPoints[1].y) : 0;
    }

    /**
     * Format the coordinates of the selection as a string as: "x1,y1 x2,y2".
     * @returns The coordinates of the selection as a formatted string.
     */
    getPointsAsString() {
        const coordinates: string[] = [];
        for (const point of this.selectedPoints)
            coordinates.push(`${point.x},${point.y}`);

        return coordinates.join(" ");
    }

    /**
     * Draw the shape of the selection on a given SVG element. Note that everything on this SVG will be overwritten.
     * @param svg - SVG HTML element on which to draw the selection.
     * @param dimensions - x and y coordinates of the top-left corner of the SVG element and its width and height.
     * @param config - Frontend config containing constants for the aesthetics of the selection.
     */
    draw(svg: d3.Selection<null, unknown, null, undefined>,
         dimensions: { x: number, y: number, width: number, height: number },
         config: FrontendConfig) {

        // Remove old selection
        svg.selectAll("*").remove();

        svg.attr("x", dimensions.x)
            .attr("y", dimensions.y)
            .attr("width", dimensions.width)
            .attr("height", dimensions.height);

        if (this.selectionType == SelectionOption.Rectangle) {
            svg.append("rect")
                .attr("x", this.getOrigin().x)
                .attr("y", this.getOrigin().y)
                .attr("width", this.getWidth())
                .attr("height", this.getHeight())
                .attr("fill", config.selectionToolConfig.fill_color)
                .attr("stroke", config.selectionToolConfig.stroke_color)
                .attr("opacity", config.selectionToolConfig.opacity);
        } else if (this.selectionType == SelectionOption.Lasso) {
            svg.append("polygon")
                .attr("points", this.getPointsAsString())
                .attr("fill", config.selectionToolConfig.fill_color)
                .attr("stroke", config.selectionToolConfig.stroke_color)
                .attr("opacity", config.selectionToolConfig.opacity);
        }
    }

}

/**
 * Supported types of selection.
 */
export enum SelectionOption {
    Lasso = "lasso",
    Rectangle = "rectangle",
}
