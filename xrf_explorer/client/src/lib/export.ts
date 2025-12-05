import { reactive } from "vue";
import { saveAs } from "file-saver";
import { toBlob } from "html-to-image";
import { sentenceCase, snakeCase } from "change-case";
import * as THREE from "three";
import { scene } from "@/components/image-viewer/scene";
import { layers } from "@/components/image-viewer/state";
import { toast } from "vue-sonner";
import { getTargetSize } from "@/components/image-viewer/api";
import { renderElementalMaps } from "@/components/image-viewer/elementalHelper";
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
  const baseSize = 1200;
  const scale = baseSize / Math.min(element.clientWidth, element.clientHeight);

  void toBlob(element, {
    style: {
      border: "none",
      backgroundColor: "hsl(var(--background))",
    },
    canvasWidth: element.clientWidth * scale,
    canvasHeight: element.clientHeight * scale,
    width: element.clientWidth,
    height: element.clientHeight,
  }).then((blob) => {
    if (blob != null) {
      saveBlob(`${datasource.value}_${name}`, blob);
    } else {
      toast.warning(sentenceCase(`Failed to export ${name}`));
    }
  });
}

/**
 * Exports the current scene.
 * Creates and download a png image to the user's device.
 * The created image is a composition of all layers in the workspace,
 * with their respective properties (Contrast, Saturation, Gamma, Brightness, Opacity and Lens visibility).
 */
export async function exportScene() {
  toast.info("Exporting painting");

  // Create a renderer for the scene
  const camera = new THREE.OrthographicCamera();
  const renderer = new THREE.WebGLRenderer({
    alpha: true,
  });

  // Set the renderer dimensions equal to the dimensions of the painting
  const size = await getTargetSize();
  renderer.setSize(size.width, size.height);

  // Store original viewport and lens uniforms for each layer
  const originalUniforms = layers.value.map((layer) => ({
    viewport: layer.uniform.iViewport.value.clone(),
    mouse: layer.uniform.uMouse.value.clone(),
    radius: layer.uniform.uRadius.value,
  }));

  // Get the current viewport dimensions from the original renderer
  const viewportWidth = scene.renderer?.domElement.width || 1;
  const viewportHeight = scene.renderer?.domElement.height || 1;

  // Transform lens coordinates from viewport space to painting space
  layers.value.forEach((layer, index) => {
    const original = originalUniforms[index];

    // Get the current viewbox (what portion of the painting is visible in the viewport)
    const viewboxX = original.viewport.x;
    const viewboxY = original.viewport.y;
    const viewboxW = original.viewport.z;
    const viewboxH = original.viewport.w;

    // Transform lens position from viewport coordinates to painting coordinates
    // original.mouse is in viewport pixel coordinates (0 to viewportWidth/Height)
    // mapping it to painting coordinates (0 to size.width/height)

    // Convert viewport pixel coordinates to normalized coordinates (0 to 1)
    const normalizedX = original.mouse.x / viewportWidth;
    const normalizedY = original.mouse.y / viewportHeight;

    // Map to the painting coordinates considering the viewbox
    const paintingX = viewboxX + normalizedX * viewboxW;
    const paintingY = viewboxY + normalizedY * viewboxH;

    // Scaling lens radius from viewport pixels to painting pixels
    // This uses the average scale factor between width and height
    const scaleX = viewboxW / viewportWidth;
    const scaleY = viewboxH / viewportHeight;
    const averageScale = (scaleX + scaleY) / 2;
    const paintingRadius = original.radius * averageScale;

    // Set the viewport to cover the entire painting
    layer.uniform.iViewport.value.set(0, 0, size.width, size.height);

    // Set the transformed lens position and radius
    layer.uniform.uMouse.value.set(paintingX, paintingY);
    layer.uniform.uRadius.value = paintingRadius;
  });

  // Store the original renderer
  const originalRenderer = scene.renderer;

  // Temporarily set the export renderer so elemental maps render with correct dimensions
  scene.renderer = renderer;

  // Render elemental maps to update the render targets before final export
  renderElementalMaps();

  // Render the painting using the created renderer
  renderer.render(scene.scene, camera);

  // Restore the original renderer
  scene.renderer = originalRenderer;

  // Restore original uniforms
  layers.value.forEach((layer, index) => {
    const original = originalUniforms[index];
    layer.uniform.iViewport.value.copy(original.viewport);
    layer.uniform.uMouse.value.copy(original.mouse);
    layer.uniform.uRadius.value = original.radius;
  });

  // Convert the rendered painting and save it to the client
  renderer.domElement.toBlob((blob) => {
    if (blob != null) {
      saveBlob(datasource.value, blob);
    } else {
      toast.warning("Failed to export painting");
    }
  });

  // Destroy the renderer
  renderer.dispose();
}

/**
 * Saves a blob from the client as an image file.
 * @param name - The name to use for the image.
 * @param blob - The blob to save to the image file.
 */
export function saveBlob(name: string, blob: Blob) {
  saveAs(blob, `${snakeCase(name)}.jpeg`);
}
