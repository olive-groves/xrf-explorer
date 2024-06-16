import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { SelectionAreaSelection, SelectionAreaType } from "./selection";

/**
 * Represent a point in 2D space.
 */
export type Point2D = {
  /**
   * Represents the X coordinate of the point.
   */
  x: number;
  /**
   * Represents the Y coordinate of the point.
   */
  y: number;
};

/**
 * Combines arrays of tailwind classes, removing duplicate and overriding classes.
 * @param inputs - Arrays of class values.
 * @returns The merged array of tailwind classes.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const remFactor = 16;

/**
 * Converts from CSS rem units to px units.
 * @param rem - A size in rem.
 * @returns The size in pixels representing the given size in rem.
 */
export function remToPx(rem: number): number {
  return rem * remFactor;
}

/**
 * Converts from CSS px units to rem units.
 * @param px - A size in px.
 * @returns The size in rem representing the given size in px.
 */
export function pxToRem(px: number): number {
  return px / remFactor;
}

/**
 * Creates a deep clone of any object.
 * @param obj - The object to clone.
 * @returns The clone of the object.
 */
export function deepClone<Type>(obj: Type): Type {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Converts hex into RGB.
 * @param hex - The hex value to convert.
 * @returns The RGB value.
 */
export function hexToRgb(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);

  return [r, g, b];
}

/**
 * Convert a single RGB component to it corresponding Hex component.
 * @param component - The value of R, G or B (0-255).
 * @returns The corresponding Hex component of the given RGB component.
 */
function rgbComponentToHex(component: number): string {
  const hex: string = component.toString(16);
  return hex.length == 1 ? `0${hex}` : hex;
}

/**
 * Converts RGB color into Hex color.
 * @param rgb - The RGB value to convert.
 * @returns The Hex equivalent of the given RGB value.
 */
export function rgbToHex(rgb: [number, number, number]): string {
  return `#${rgbComponentToHex(rgb[0])}${rgbComponentToHex(rgb[1])}${rgbComponentToHex(rgb[2])}`;
}

/**
 * Resets the window.
 */
export function resetWindow() {
  window.location.reload();
}

/**
 * Removes a specific value from an array.
 * @param array - The array to remove the value from.
 * @param value - The value to remove.
 */
export function removeValue<Type>(array: Type[], value: Type) {
  const index = array.indexOf(value);
  if (index > -1) {
    array.splice(index);
  }
}

/**
 * Sorts the points of a rectangle selection, putting the minimal coordinates in the first point.
 * @param points - The points to sort.
 * @returns The sorted point coordinates.
 */
export function sortRectanglePoints(points: Point2D[]): Point2D[] {
  return [
    {
      x: Math.min(points[0].x, points[1].x),
      y: Math.min(points[0].y, points[1].y),
    },
    {
      x: Math.max(points[0].x, points[1].x),
      y: Math.max(points[0].y, points[1].y),
    },
  ];
}

/**
 * Flips the y coordinates of a list of points.
 * @param points - The points to flip.
 * @param height - The height of the area to flip, 0 -> height and height -> 0.
 * @returns The list of flipped points.
 */
function flipPoints(points: Point2D[], height: number): Point2D[] {
  return points.map<Point2D>((point) => {
    return {
      x: point.x,
      y: (height ?? 0) - point.y,
    };
  });
}

/**
 * Flips a selection.
 * @param selection - The selection to flip.
 * @param height - The height of the area to flip, 0 -> height and height -> 0.
 * @returns The flipped selection.
 */
export function flipSelectionAreaSelection(selection: SelectionAreaSelection, height: number): SelectionAreaSelection {
  switch (selection.type) {
    case SelectionAreaType.Lasso: {
      return {
        type: SelectionAreaType.Lasso,
        points: flipPoints(selection.points, height),
      };
    }
    case SelectionAreaType.Rectangle: {
      return {
        type: SelectionAreaType.Rectangle,
        points: sortRectanglePoints(flipPoints(selection.points, height)),
      };
    }
    default: {
      return {
        type: undefined,
        points: [],
      };
    }
  }
}
