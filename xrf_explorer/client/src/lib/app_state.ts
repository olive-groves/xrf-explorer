import { reactive } from "vue";
import { WorkspaceConfig } from "./workspace";

/**
 * Reactive value that contains the current appstate.
 * Use computed() in components to access properties of this state.
 */
export const appState = reactive<AppState>({});

/**
 * Type describing the state of the client.
 * Solely intended for data that needs to be accessed from many different unrelated components.
 */
export type AppState = {
  /**
   * The current workspace.
   */
  workspace?: WorkspaceConfig;
};
