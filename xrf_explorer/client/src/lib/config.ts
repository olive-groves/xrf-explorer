/**
 * Type declaration for the client configuration.
 */
export type FrontendConfig = {
  /**
   * Configuration related to calling the api.
   */
  api: ApiConfig;
  /**
   * Configuration related to the image viewer.
   */
  imageViewer: ImageViewerConfig;
  /**
   * Configuration related to uploading.
   */
  upload: UploadConfig;
  /**
   * Configuration related to the selection tool.
   */
  selectionToolConfig: SelectionToolConfig;
};

/**
 * Type declaration for upload configuration.
 */
export type UploadConfig = {
  /**
   * The size (in bytes) of the chunks into which each file will be split before being uploaded to the server.
   */
  uploadChunkSizeInBytes: number;
};

/**
 * Type declaration for the api connectivity configuration.
 */
export type ApiConfig = {
  /**
   * The endpoint which the client can connect to .
   */
  endpoint: string;
};

/**
 * Type declaration for the image viewer configuration.
 */
export type ImageViewerConfig = {
  /**
   * Default multiplier for the movement speed in the image viewer.
   */
  defaultMovementSpeed: number;
  /**
   * Default multiplier for the scroll speed in the image viewer.
   */
  defaultScrollSpeed: number;
  /**
   * The default size of the lens in the image viewer.
   */
  defaultLensSize: number;
  /**
   * The maximum(/minimum) zoom level in the image viewer.
   */
  zoomLimit: number;
};

/**
 * Type declaration for the selection tool configuration.
 */
export type SelectionToolConfig = {
  /**
   * Mouse button that will add the current location point to the current selection.
   */
  addPointButton: number;
  /**
   * Mouse button that will cancel the current selection.
   */
  cancelButton?: number;
  /**
   * Keyboard key that will cancel the current selection.
   */
  cancelKey?: string;
  /**
   * Mouse button that will consolidate the current selection (not applicable to rectangle selection).
   */
  confirmButton?: number
  /**
   * Keyboard key that will consolidate the current selection (not applicable to rectangle selection).
   */
  confirmKey?: string;
  /**
   * Color in which the selected area should be displayed.
   */
  fill_color: string;
  /**
   * Color of the outline of the selected area.
   */
  stroke_color: string;
  /**
   * Set the opacity of the selection overlay.
   */
  opacity: number;
};

/**
 * The default configuration for the client.
 */
export const DefaultConfig: FrontendConfig = {
  api: {
    endpoint: "/api",
  },
  imageViewer: {
    defaultMovementSpeed: 1.0,
    defaultScrollSpeed: 1.0,
    defaultLensSize: 100.0,
    zoomLimit: 4.0,
  },
  upload: {
    uploadChunkSizeInBytes: 50000000, // 50 MB
  },
  selectionToolConfig: {
    addPointButton: 0, // left mouse button
    cancelButton: null,
    cancelKey: "Escape",
    confirmButton: null,
    confirmKey: "Enter",
    fill_color: "#FFEF00", // shoutout to the canary islands
    stroke_color: "#000000", // black
    opacity: 0.5,
  },
};

/**
 * Get the configuration for the frontend.
 *
 * This will be provided by the App.vue component and can be accessed using
 * `const config = inject<FrontendConfig>("config")!`. (note the exclamation mark)
 * This function should hence not be used elsewhere.
 * @returns The frontend configuration.
 */
export async function getConfig(): Promise<FrontendConfig> {
  return DefaultConfig;
}
