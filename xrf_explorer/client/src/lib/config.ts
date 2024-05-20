import { BasicColorMode } from "@vueuse/core";

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
   * The default theme of the client.
   */
  defaultTheme: BasicColorMode;
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
};

/**
 * The default configuration for the client.
 */
export const DefaultConfig: FrontendConfig = {
  api: {
    endpoint: "http://localhost:8001/api",
  },
  imageViewer: {
    defaultMovementSpeed: 2.0,
    defaultScrollSpeed: 1.0,
    defaultLensSize: 100.0,
  },
  defaultTheme: "dark",
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
