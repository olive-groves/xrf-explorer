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
