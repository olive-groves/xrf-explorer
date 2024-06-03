import { reactive } from "vue";
import { saveAs } from "file-saver";
import domToImage from "dom-to-image-more";
import { snakeCase } from "change-case";
import * as THREE from "three";
import { scene } from "@/components/image-viewer/scene";
import { layers } from "@/components/image-viewer/state";
import { toast } from "vue-sonner";
import { getTargetSize } from "@/components/image-viewer/api";
import { datasource } from "./appState";

/**
 * Contains the list of exportable elements that should be shown in the export menu.
 */
export const exportableElements = reactive<{
  [key: string]: HTMLElement | undefined;
}>({});

/**
 * Exports a given HTML Element as a png.
 * @param name - The name to give the downloaded png file.
 * @param element - The element to convert to a png.
 */
export function exportElement(name: string, element: HTMLElement) {
  const scale = 4;

  domToImage
    .toBlob(element, {
      style: {
        border: "none",
        backgroundColor: "hsl(var(--background))",
      },
      width: element.clientWidth * scale,
      height: element.clientHeight * scale,
    })
    .then((blob) => {
      saveBlob(`${datasource.value}_${name}`, blob);
    });
}

/**
 * Export the scene.
 */
export async function exportScene() {
  toast.info("Exporting painting");

  const camera = new THREE.OrthographicCamera();
  const renderer = new THREE.WebGLRenderer({
    alpha: true,
  });

  const size = await getTargetSize();

  renderer.setSize(size.width, size.height);

  layers.value.forEach((layer) => {
    layer.uniform.iViewport.value.set(0, 0, size.width, size.height);
  });

  renderer.render(scene.scene, camera);

  renderer.domElement.toBlob((blob) => {
    if (blob != null) {
      saveBlob(datasource.value, blob);
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
