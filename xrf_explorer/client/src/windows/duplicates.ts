import { SelectionAreaSelection, SelectionAreaType } from "@/lib/selection";

/**
 * Returns a request body for selecting the entire area based on the given size.
 * @param width - The width of the area.
 * @param height - The height of the area.
 * @returns A SelectionAreaSelection object representing the entire area.
 */
export function returnRequestBodyRectangle(width: number, height: number) {
  const request_body: SelectionAreaSelection = {
    type: SelectionAreaType.Rectangle,
    points: [
      { x: 0, y: 0 },
      { x: width, y: height },
    ],
  };
  return request_body;
}
