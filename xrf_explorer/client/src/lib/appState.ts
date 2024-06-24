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
  secondViewer: false,
});

/**
 * Some useful variables directly computed from appState.
 * Readonly, for writing you need to directly modify appState.
 */
export const datasource = computed(() => appState.workspace?.name ?? "");
export const elements = computed(
  () => appState.workspace?.elementalChannels.filter((element) => element.enabled) ?? [],
);
export const low = computed(() => appState.workspace?.spectralParams?.low ?? 0);
export const high = computed(() => appState.workspace?.spectralParams?.high ?? 40);
export const binSize = computed(() => appState.workspace?.spectralParams?.binSize ?? 1);
export const binned = computed(() => appState.workspace?.spectralParams?.binned ?? false);

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
   * Whether the second viewer is enabled.
   */
  secondViewer: boolean;
};
