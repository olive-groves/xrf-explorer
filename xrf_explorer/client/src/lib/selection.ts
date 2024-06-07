import * as d3 from "d3";
import { Point2D } from "@/components/image-viewer/types.ts";
import { FrontendConfig } from "@/lib/config.ts";

/**
 * Type describing the current selection.
 * This is intended to be used to describe all the simultaneous selections.
 */
export type Selection = {
  /**
   * The selection made by the lens tool.
   * Will be null if the lens tool is not active.
   */
  lens: CircleSelection | null;
  /**
   * The selection of rectangles made in the image viewer.
   * Will be an empty array if no rectangle selection is active.
   */
  rectangles: RectangleSelection[];
  /**
   * The selection of elements made.
   */
  elements: ElementSelection[];
  /**
   * The selection made in the color segmentation window.
   */
  colorSegmentation: ColorSegmentationSelection[];
  /**
   * The selection made in the dimensionality reduction window.
   * Will be null if there is no active dimensionality reduction selection.
   */
  dimensionalityReduction: DimensionalityReductionSelection | null;
};

/**
 * Describes a circle by center and radius.
 */
export type CircleSelection = {
  /**
   * The center coordinates of the selection.
   */
  center: number;
  /**
   * The radius of the selection.
   */
  radius: number;
};

/**
 * Describes a selected rectangle using two opposite corners.
 */
export type RectangleSelection = {
  /**
   * The x coordinate of the first corner.
   */
  x1: number;
  /**
   * The y coordinate of the first corner.
   */
  y1: number;
  /**
   * The x coordinate of the second corner.
   */
  x2: number;
  /**
   * The y coordinate of the second corner.
   */
  y2: number;
};

/**
 * Describes an element.
 */
export type ElementSelection = {
  /**
   * The channel of the element.
   */
  channel: number;
  /**
   * Checks if elemental channel is selected.
   */
  selected: boolean;
  /**
   * The color associated with the element.
   */
  color: string;
  /**
   * The thresholds for the element.
   */
  thresholds: [number, number];
};

/**
 * Describes the selected color segmentation segments.
 */
export type ColorSegmentationSelection = {
  /**
   * The element corresponding to the clusters.
   * If no element, then element should be one more than the highest element index.
   */
  element: number;
  /**
   * Whether the element is selected.
   */
  selected: boolean;
  /**
   * Whether each cluster is enabled.
   */
  enabled: boolean[];
  /**
   * The color associated with each cluster.
   */
  colors: string[];
};

/**
 * Describes the dimensionality reduction selection.
 */
export type DimensionalityReductionSelection = {
  /**
   * The type of selection being used (Rectangle, Lasso, etc.)
   */
  selectionType: SelectionOption;
  /**
   * The list of points that make up the selection.
   */
  points: Point2D[];
  /**
   * The width and height of the embedded image on which the selection is made.
   */
  embeddedImageDimensions: { width: number; height: number };
};

/**
 * Supported types of selection.
 */
export enum SelectionOption {
    Lasso = "lasso",
    Rectangle = "rectangle",
}

/**
 * Blueprint parent class for all selection tools.
 */
abstract class BaseSelectionTool {
  /**
   * Determines the type of selection the tool should perform (rectangle, lasso, etc.).
   */
  protected selectionType: SelectionOption;
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

  protected constructor(selectionType: SelectionOption) {
    this.selectionType = selectionType;
  }

  type(): SelectionOption {
    return this.selectionType;
  }

  cancelSelection(): void {
    this.selectedPoints = [];
    this.activeSelection = false;
    this.finishedSelection = false;
  }

  /**
   * Set the necessary values to mark the selection as complete.
   */
  confirmSelection(): void {
    this.activeSelection = false;
    this.finishedSelection = true;
  }

  protected handleSelection(): void {}

  addPointToSelection(newPoint: Point2D): void {
    // restart selection if the current selection is complete
    if (this.finishedSelection)
      this.cancelSelection();

    // we're adding a new point so regardless of the state the user is definitely actively editing the selection.
    this.activeSelection = true;
    // add the new point to the selection
    this.selectedPoints.push(newPoint);

    // handle edge cases specific to the selection type
    this.handleSelection();
  }

  protected resetSVGDrawing(svg: d3.Selection<null, unknown, null, undefined>,
                  dimensions: { x: number, y: number, width: number, height: number }):
      d3.Selection<null, unknown, null, undefined> {
    svg.selectAll("*").remove();

    svg.attr("x", dimensions.x)
            .attr("y", dimensions.y)
            .attr("width", dimensions.width)
            .attr("height", dimensions.height);

    return svg;
  }

  abstract draw(svg: d3.Selection<null, unknown, null, undefined>,
       dimensions: { x: number, y: number, width: number, height: number },
       config: FrontendConfig): void
}

/**
 * Implements all functionality for the rectangle variant of the selection tool. Inherits from `BaseSelectionTool`.
 */
export class RectangleSelectionTool extends BaseSelectionTool {
  constructor() {
    super(SelectionOption.Rectangle);
  }

  /**
   * Update the list of points to achieve a list of format `[top-left, bottom-right]`.
   */
  protected handleSelection(): void {
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
   * Get the point of origin of the selection.
   * @returns The top-left point of the selection.
   */
  originPoint(): Point2D {
    return this.selectedPoints[0];
  }

  /**
   * Get the width of the selection (Rectangle selection only).
   * @returns The width of the selection for Rectangle selection, 0 otherwise.
   */
  width(): number {
    return (this.selectedPoints.length == 2) ? Math.abs(this.selectedPoints[0].x - this.selectedPoints[1].x) : 0;
  }

  /**
   * Get the height of the selection (Rectangle selection only).
   * @returns The height of the selection for Rectangle selection, 0 otherwise.
   */
  height(): number {
      return (this.selectedPoints.length == 2) ? Math.abs(this.selectedPoints[0].y - this.selectedPoints[1].y) : 0;
  }

  /**
   * Draw the selection rectangle on a given SVG element. Note that everything on this SVG will be overwritten.
   * @param svg - SVG HTML element on which to draw the selection.
   * @param dimensions - x and y coordinates of the top-left corner of the SVG element and its width and height.
   * @param config - Frontend config containing constants for the aesthetics of the selection.
   */
  draw(svg: d3.Selection<null, unknown, null, undefined>,
       dimensions: { x: number, y: number, width: number, height: number },
       config: FrontendConfig): void {
    svg = this.resetSVGDrawing(svg, dimensions);
    if (this.finishedSelection)
      svg.append("rect")
        .attr("x", this.originPoint().x)
        .attr("y", this.originPoint().y)
        .attr("width", this.width())
        .attr("height", this.height())
        .attr("fill", config.selectionToolConfig.fill_color)
        .attr("stroke", config.selectionToolConfig.stroke_color)
        .attr("opacity", config.selectionToolConfig.opacity);
  }
}

/**
 * Implements the lasso variant of the selection tool. Inherits from `BaseSelectionTool`.
 */
export class LassoSelectionTool extends BaseSelectionTool {
  constructor() {
    super(SelectionOption.Lasso);
  }

  /**
   * Update the list of points to avoid colliding areas.
   */
  handleSelection(): void {
    // TODO: i have no clue how to actually do this
  }

  /**
   * Format the coordinates of the selection as a string as: "x1,y1 x2,y2".
   * @returns The coordinates of the selection as a formatted string.
   */
  getPointsAsString(): string {
    const coordinates: string[] = [];
    for (const point of this.selectedPoints)
        coordinates.push(`${point.x},${point.y}`);

    return coordinates.join(" ");
  }

  /**
   * Draw the selection polygon on a given SVG element. Note that everything on this SVG will be overwritten.
   * @param svg - SVG HTML element on which to draw the selection.
   * @param dimensions - x and y coordinates of the top-left corner of the SVG element and its width and height.
   * @param config - Frontend config containing constants for the aesthetics of the selection.
   */
  draw(svg: d3.Selection<null, unknown, null, undefined>,
       dimensions: { x: number, y: number, width: number, height: number },
       config: FrontendConfig): void {
    svg = this.resetSVGDrawing(svg, dimensions);
    svg.append("polygon")
      .attr("points", this.getPointsAsString())
      .attr("fill", config.selectionToolConfig.fill_color)
      .attr("stroke", config.selectionToolConfig.stroke_color)
      .attr("opacity", config.selectionToolConfig.opacity);
  }
}
