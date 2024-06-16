import { SelectionAreaType } from "@/lib/selection";
import { Point2D } from "@/lib/utils";

/**
 * Used to fetch averages from the backend when using a selection
 * Points are the points of the selection. In case of rectangle selection,
 * those are two opposite corners of the rectangle. In case of lasso selection,
 * those are the points in the order in which they form the selection area.
 */
export interface RequestBody {
  /**
   *The type of the selection.
   */
  type: SelectionAreaType | undefined;
  /**
   * The list of points defining the selected area.
   */
  points: Point2D[];
}
