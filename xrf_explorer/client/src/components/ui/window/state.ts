import { reactive } from "vue";

/**
 * Describes the location of a window.
 */
export type WindowLocation = "left" | "right";

/**
 * Contains the app-wide state of a window.
 */
export type WindowState = {
  /**
   * The id of the window, automatically generated from the title.
   */
  id: string;
  /**
   * The title of the window.
   */
  title: string;
  /**
   * If the content of the window should be scrollable.
   */
  scrollable: boolean;
  /**
   * If the window has been disabled.
   */
  disabled: boolean;
  /**
   * If the window has been opened.
   */
  opened: boolean;
  /**
   * When the window is open, this is its location.
   */
  location: WindowLocation;
  /**
   * Indicates whether the portal target for the window currently exists.
   */
  portalMounted: boolean;
};

export const windowState = reactive<{
  [key: string]: WindowState;
}>({});

/**
 * Contains the window-specific state local to one of the side panels.
 */
export type SidepanelWindowState = {
  /**
   * The title of the window.
   */
  title: string;
  /**
   * The index of the window when sorted from top to bottom.
   */
  index: number;
  /**
   * Whether the window is minimized or maximized.
   */
  minimized: boolean;
  /**
   * The current total height of the window in pixels.
   */
  height: number;
  /**
   * The maximum allowed height for the window based on the size of its content.
   */
  maxContentHeight: number;
};
