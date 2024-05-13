import { reactive } from "vue";

export type WindowLocation = "left" | "right";

export type WindowState = {
  id: string;
  title: string;
  scrollable: boolean;
  opened: boolean;
  location: WindowLocation;
  portalMounted: boolean;
};

export const windowState = reactive<{
  [key: string]: WindowState;
}>({});

export type SidepanelWindowState = {
  title: string;
  index: number;
  minimized: boolean;
  height: number;
  maxContentHeight: number;
};
