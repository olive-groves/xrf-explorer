import { reactive } from "vue";
import { saveAs } from "file-saver";
import domToImage from "dom-to-image-more";
import { snakeCase } from "change-case";

/**
 * Contains the list of exportable elements that should be shown in the export menu.
 */
export const exportableElements = reactive<{
  [key: string]: HTMLElement;
}>({});

/**
 * Exports a given HTML Element as a png.
 * @param name - The name to give the downloaded png file.
 * @param element - The element to convert to a png.
 */
export function exportToImage(name: string, element: HTMLElement) {
  // The minimum dimension of the export image
  const baseSize = 512;

  const scale = Math.max(1.0, baseSize / element.clientWidth, baseSize / element.clientHeight);

  domToImage
    .toBlob(element, {
      width: element.clientWidth * scale,
      height: element.clientHeight * scale,
    })
    .then((blob) => {
      saveBlob(name, blob);
    });
}

/**
 * Saves a blob from the client as an image file.
 * @param name - The name to use for the image.
 * @param blob - The blob to save to the image file.
 */
export function saveBlob(name: string, blob: Blob) {
  saveAs(blob, `${snakeCase(name)}.png`);
}
