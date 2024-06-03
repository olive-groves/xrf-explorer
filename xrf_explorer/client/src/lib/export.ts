import { reactive } from "vue";
import { saveAs } from "file-saver";
import domToImage from "dom-to-image-more";
import { snakeCase } from "change-case";
import * as THREE from "three";
import { scene } from "@/components/image-viewer/scene";
import { layers } from "@/components/image-viewer/state";
import { toast } from "vue-sonner";

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
export function exportElement(name: string, element: HTMLElement) {
  domToImage
    .toBlob(element, {
      width: element.clientWidth,
      height: element.clientHeight,
    })
    .then((blob) => {
      saveBlob(name, blob);
    });
}

/**
 * Export the scene.
 */
export function exportScene() {
  toast.info("Starting painting export", {
    description: "This may take up to a minute",
  });

  const camera = new THREE.OrthographicCamera();
  const renderer = new THREE.WebGLRenderer({
    alpha: true,
  });

  renderer.setSize(5017, 5928);

  layers.value.forEach((layer) => {
    layer.uniform.iViewport.value.set(0, 0, 1, 5928 / 5017);
  });

  renderer.render(scene.scene, camera);

  renderer.domElement.toBlob((blob) => {
    if (blob != null) {
      saveBlob("image.png", blob);
    } else {
      toast.warning("Failed to export painting");
    }
  });
}

/**
 * Saves a blob from the client as an image file.
 * @param name - The name to use for the image.
 * @param blob - The blob to save to the image file.
 */
export function saveBlob(name: string, blob: Blob) {
  saveAs(blob, `${snakeCase(name)}.jpeg`);
}
