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
   * Will be null if there is no active color segmentation selection.
   */
  colorSegmentation: ColorSegmentationSelection | null;
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
export type ColorSegmentationSelection = null;

/**
 * Describes the dimensionality reduction selection.
 */
export type DimensionalityReductionSelection = null;
