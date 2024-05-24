import { reactive } from "vue";
import { WorkspaceConfig } from "./workspace";
import { Selection } from "./selection";

/**
 * Reactive value that contains the current appstate.
 * Use computed() in components to read properties of this state.
 */
export const appState = reactive<AppState>({
  selection: {
    lens: null,
    rectangles: [],
    elements: [],
    colorSegmentation: null,
    dimensionalityReduction: null,
  },
});

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
};
