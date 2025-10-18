import { computed, reactive } from "vue";
import { WorkspaceConfig } from "./workspace";
import { Selection } from "./selection";

/**
 * Reactive value that contains the current appstate.
 * Use computed() in components to read properties of this state.
 */
export const appState = reactive<AppState>({
  selection: {
    imageViewer: {
      type: undefined,
      points: [],
    },
    elements: [],
    colorSegmentation: {
      element: 0,
      enabled: Array(1).fill(false),
      colors: [],
      k: 20,
      threshold: 20,
    },
    dimensionalityReduction: {
      color: "#ffffff",
      area: {
        type: undefined,
        points: [],
      },
    },
  },
});

/**
 * Deprecated compatibility helpers — prefer `workspace.stitchingMode`.
 */
Object.defineProperty(appState, "stitching", {
  get() {
    return (appState.workspace?.stitchingMode ?? "full") === "partial";
  },
  set(v: boolean) {
    if (!appState.workspace) return;
    appState.workspace.stitchingMode = v ? "partial" : "full";
  },
  configurable: true,
});

/**
 * Some useful variables directly computed from appState.
 * Readonly, for writing you need to directly modify appState.
 */
export const datasource = computed(() => appState.workspace?.name ?? "");
export const elements = computed(
  () => appState.workspace?.elementalChannels.filter((element) => element.enabled) ?? [],
);
export const elementalDataPresent = computed(() => (appState.workspace?.elementalCubes.length ?? 0) > 0);
export const spectralDataPresent = computed(() => (appState.workspace?.spectralCubes.length ?? 0) > 0);

/**
 * Type describing the state of the client.
 * Solely intended for data that needs to be accessed from many different unrelated components.
 */
export type AppState = {
  /**
   * The current workspace.
   */
  workspace?: WorkspaceConfig;
  /**
   * The active selection.
   */
  selection: Selection;
  /**
   * Whether the stitching viewer is enabled
   */
  // deprecated: keep the property documented for older code paths. Prefer workspace.stitchingMode.
  stitching?: boolean;
};
