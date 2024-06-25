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
  colorSegmentation: ColorSegmentationSelection;
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
   * The element index corresponding to the clusters
   * If whole painting, it's 0, otherwise it's the
   * element's channel plus 1.
   */
  element: number;
  /**
   * Whether each cluster is enabled.
   */
  enabled: boolean[];
  /**
   * The color associated with each cluster.
   */
  colors: string[];
  /**
   * The number of clusters to compute.
   */
  k: number;
  /**
   * The elemental threshold parameter for the k-means algorithm,
   * range from 0 to 100.
   * Arbitrary number if computing clusters over the whole image.
   */
  threshold: number;
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
  Polygon = "polygon",
  Rectangle = "rectangle",
}
