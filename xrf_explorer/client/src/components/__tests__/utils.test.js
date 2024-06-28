import { describe, expect, test } from 'vitest'
import { hexToRgb, rgbToHex, sortRectanglePoints } from "@/lib/utils";

describe('hexToRgb and rgbToHex Test', () => {
    const color1 = {rgb: [77, 184, 39], hex: "#4db827"}
    const color2 = {rgb: [158, 87, 153], hex: "#9e5799"}

    const black = {rgb: [0, 0, 0], hex: "#000000"}
    const white = {rgb: [255, 255, 255], hex: "#ffffff"}

    const red = {rgb: [255, 0, 0], hex: "#ff0000"}
    const green = {rgb: [0, 255, 0], hex: "#00ff00"}
    const blue = {rgb: [0, 0, 255], hex: "#0000ff"}

    test('random colors hex to rgb', () => {
        expect(hexToRgb(color1.hex)).toStrictEqual(color1.rgb)
        expect(hexToRgb(color2.hex)).toStrictEqual(color2.rgb)
    })

    test('random colors rgb to hex', () => {
        expect(rgbToHex(color1.rgb)).toStrictEqual(color1.hex)
        expect(rgbToHex(color2.rgb)).toStrictEqual(color2.hex)
    })

    test('black white color hex to rgb', () => {
        expect(hexToRgb(black.hex)).toStrictEqual(black.rgb)
        expect(hexToRgb(white.hex)).toStrictEqual(white.rgb)
    })

    test('black white color rgb to hex', () => {
        expect(rgbToHex(black.rgb)).toStrictEqual(black.hex)
        expect(rgbToHex(white.rgb)).toStrictEqual(white.hex)
    })

    test('red green blue color hex to rgb', () => {
        expect(hexToRgb(red.hex)).toStrictEqual(red.rgb)
        expect(hexToRgb(green.hex)).toStrictEqual(green.rgb)
        expect(hexToRgb(blue.hex)).toStrictEqual(blue.rgb)
    })

    test('red green blue color rgb to hex', () => {
        expect(rgbToHex(red.rgb)).toStrictEqual(red.hex)
        expect(rgbToHex(green.rgb)).toStrictEqual(green.hex)
        expect(rgbToHex(blue.rgb)).toStrictEqual(blue.hex)
    })
})

describe('sortRectanglePoints Test', () => {
    const signs = [-1, 1]
    const theRectangle = [{x: -1, y: -1}, {x: 1, y: 1}]
    test('sortRectanglePoints', () => {

        signs.forEach(e => {
            signs.forEach(f => {
                const point1 = {x: e, y: f}
                const point2 = {x: -e, y: -f}
                
                expect(sortRectanglePoints([point1, point2])).toStrictEqual(theRectangle)
            })
        });

    })
})