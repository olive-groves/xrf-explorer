import { Point2D } from "@/lib/utils";

/**
 * Type describing the current selection.
 * This is intended to be used to describe all the simultaneous selections.
 */
export type Selection = {
  /**
   * The selection made in the image viewer.
   */
  imageViewer: SelectionAreaSelection;
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
   */
  dimensionalityReduction: DimensionalityReductionSelection;
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
 * Describes a selection made in the DR Window.
 */
export type DimensionalityReductionSelection = {
  /**
   * The color of the highlighted points.
   */
  color: string;
  /**
   * The selected area.
   */
  area: SelectionAreaSelection;
};

/**
 * Describes a selection made by a selection area.
 */
export type SelectionAreaSelection = {
  /**
   * The type of selection.
   * Undefined if there is no finalized selection.
   */
  type?: SelectionAreaType;
  /**
   * The points in the selection.
   */
  points: Point2D[];
};

/**
 * Supported types of selection by the selection tool.
 */
export enum SelectionAreaType {
  Lasso = "lasso",
  Rectangle = "rectangle",
}
