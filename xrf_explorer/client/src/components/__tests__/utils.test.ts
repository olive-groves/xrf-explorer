import { describe, expect, test } from "vitest";
import { SelectionAreaSelection, SelectionAreaType } from "@/lib/selection.ts";
import {
  hexToRgb,
  rgbToHex,
  sortRectanglePoints,
  remToPx,
  pxToRem,
  cn,
  deepClone,
  flipSelectionAreaSelection,
} from "@/lib/utils";

describe("hexToRgb and rgbToHex Test", () => {
  const color1 = { rgb: [77, 184, 39] as [number, number, number], hex: "#4db827" };
  const color2 = { rgb: [158, 87, 153] as [number, number, number], hex: "#9e5799" };

  const black = { rgb: [0, 0, 0] as [number, number, number], hex: "#000000" };
  const white = { rgb: [255, 255, 255] as [number, number, number], hex: "#ffffff" };

  const red = { rgb: [255, 0, 0] as [number, number, number], hex: "#ff0000" };
  const green = { rgb: [0, 255, 0] as [number, number, number], hex: "#00ff00" };
  const blue = { rgb: [0, 0, 255] as [number, number, number], hex: "#0000ff" };

  test("random colors hex to rgb", () => {
    expect(hexToRgb(color1.hex)).toStrictEqual(color1.rgb);
    expect(hexToRgb(color2.hex)).toStrictEqual(color2.rgb);
  });

  test("random colors rgb to hex", () => {
    expect(rgbToHex(color1.rgb)).toStrictEqual(color1.hex);
    expect(rgbToHex(color2.rgb)).toStrictEqual(color2.hex);
  });

  test("black white color hex to rgb", () => {
    expect(hexToRgb(black.hex)).toStrictEqual(black.rgb);
    expect(hexToRgb(white.hex)).toStrictEqual(white.rgb);
  });

  test("black white color rgb to hex", () => {
    expect(rgbToHex(black.rgb)).toStrictEqual(black.hex);
    expect(rgbToHex(white.rgb)).toStrictEqual(white.hex);
  });

  test("red green blue color hex to rgb", () => {
    expect(hexToRgb(red.hex)).toStrictEqual(red.rgb);
    expect(hexToRgb(green.hex)).toStrictEqual(green.rgb);
    expect(hexToRgb(blue.hex)).toStrictEqual(blue.rgb);
  });

  test("red green blue color rgb to hex", () => {
    expect(rgbToHex(red.rgb)).toStrictEqual(red.hex);
    expect(rgbToHex(green.rgb)).toStrictEqual(green.hex);
    expect(rgbToHex(blue.rgb)).toStrictEqual(blue.hex);
  });
});

describe("sortRectanglePoints Test", () => {
  const signs = [-1, 1];
  const theRectangle = [
    { x: -1, y: -1 },
    { x: 1, y: 1 },
  ];

  test("sortRectanglePoints", () => {
    signs.forEach((e) => {
      signs.forEach((f) => {
        const point1 = { x: e, y: f };
        const point2 = { x: -e, y: -f };

        expect(sortRectanglePoints([point1, point2])).toStrictEqual(theRectangle);
      });
    });
  });
});

describe("remToPx and pxToRem Test", () => {
  const CSS1 = { rem: 1, px: 16 };
  const CSS2 = { rem: 108, px: 1728 };

  const CSSzero = { rem: 0, px: 0 };

  const CSSnegative = { rem: -1, px: -16 };

  const CSSlarge = { rem: 1000000, px: 16000000 };

  test("random CSS rem to px unit", () => {
    expect(remToPx(CSS1.rem)).toStrictEqual(CSS1.px);
    expect(remToPx(CSS2.rem)).toStrictEqual(CSS2.px);
  });

  test("random CSS px to rem", () => {
    expect(pxToRem(CSS1.px)).toStrictEqual(CSS1.rem);
    expect(pxToRem(CSS2.px)).toStrictEqual(CSS2.rem);
  });

  test("CSS zero rem to px unit", () => {
    expect(remToPx(CSSzero.rem)).toStrictEqual(CSSzero.px);
  });

  test("CSS zero px to rem", () => {
    expect(pxToRem(CSSzero.px)).toStrictEqual(CSSzero.rem);
  });

  test("CSS negative rem to px unit", () => {
    expect(remToPx(CSSnegative.rem)).toStrictEqual(CSSnegative.px);
  });

  test("CSS negative px to rem", () => {
    expect(pxToRem(CSSnegative.px)).toStrictEqual(CSSnegative.rem);
  });

  test("CSS large rem to px unit", () => {
    expect(remToPx(CSSlarge.rem)).toStrictEqual(CSSlarge.px);
  });

  test("CSS large px to rem", () => {
    expect(pxToRem(CSSlarge.px)).toStrictEqual(CSSlarge.rem);
  });
});

describe("cn Test", () => {
  const classes1 = ["text-red-500", "bg-blue-200"];
  const classes2 = ["font-bold", "text-lg"];
  const classes3 = ["bg-blue-200", "text-2"];

  const expected1 = "text-red-500 bg-blue-200";
  const expected2 = "font-bold text-lg";
  const expected3 = "bg-blue-200 text-2";

  test("text color and background color", () => {
    expect(cn(classes1)).toStrictEqual(expected1);
  });

  test("font type and text size", () => {
    expect(cn(classes2)).toStrictEqual(expected2);
  });

  test("background color and text size", () => {
    expect(cn(classes3)).toStrictEqual(expected3);
  });
});

describe("deepClone Test", () => {
  const obj1 = { name: "John", age: 30 };
  const clonedObj1 = deepClone(obj1);

  const obj2 = { foo: { bar: "baz" } };
  const clonedObj2 = deepClone(obj2);

  const obj3 = [1, 2, 3];
  const clonedObj3 = deepClone(obj3);

  const objEmpty = {};
  const clonedObjEmpty = deepClone(objEmpty);

  const objModif = { name: "John", age: 30 };
  const clonedObjModif = deepClone(objModif);

  test("deepClone name and age", () => {
    expect(clonedObj1).toEqual(obj1);
    expect(clonedObj1).not.toBe(obj1);
  });

  test("deepClone foo", () => {
    expect(clonedObj2).toEqual(obj2);
    expect(clonedObj2).not.toBe(obj2);
  });

  test("deepClone number array", () => {
    expect(clonedObj3).toEqual(obj3);
    expect(clonedObj3).not.toBe(obj3);
  });

  test("deepClone empty object", () => {
    expect(clonedObjEmpty).toEqual(objEmpty);
    expect(clonedObjEmpty).not.toBe(objEmpty);
  });

  test("deepClone and modify original object", () => {
    objModif.name = "Jane";
    objModif.age = 25;

    expect(clonedObjModif).toEqual({ name: "John", age: 30 });
  });
});

describe("flipSelectionAreaSelection Test", () => {
  const height = 100;

  const polygonSelection: SelectionAreaSelection = {
    type: SelectionAreaType.Polygon,
    points: [
      { x: 10, y: 20 },
      { x: 30, y: 40 },
      { x: 50, y: 60 },
    ],
  };

  const rectangleSelection: SelectionAreaSelection = {
    type: SelectionAreaType.Rectangle,
    points: [
      { x: 10, y: 20 },
      { x: 30, y: 40 },
    ],
  };

  const emptySelection: SelectionAreaSelection = {
    type: undefined,
    points: [],
  };

  test("flip polygon selection", () => {
    const flippedPolygonSelection = flipSelectionAreaSelection(polygonSelection, height);
    const expectedFlippedPolygonSelection: SelectionAreaSelection = {
      type: SelectionAreaType.Polygon,
      points: [
        { x: 10, y: 80 },
        { x: 30, y: 60 },
        { x: 50, y: 40 },
      ],
    };
    expect(flippedPolygonSelection).toEqual(expectedFlippedPolygonSelection);
  });

  test("flip rectangle selection", () => {
    const flippedRectangleSelection = flipSelectionAreaSelection(rectangleSelection, height);
    const expectedFlippedRectangleSelection: SelectionAreaSelection = {
      type: SelectionAreaType.Rectangle,
      points: [
        { x: 10, y: 60 },
        { x: 30, y: 80 },
      ],
    };
    expect(flippedRectangleSelection).toEqual(expectedFlippedRectangleSelection);
  });

  test("flip empty selection", () => {
    const flippedEmptySelection = flipSelectionAreaSelection(emptySelection, height);
    const expectedFlippedEmptySelection: SelectionAreaSelection = {
      type: undefined,
      points: [],
    };
    expect(flippedEmptySelection).toEqual(expectedFlippedEmptySelection);
  });
});
