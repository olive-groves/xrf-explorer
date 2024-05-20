import { reactive } from "vue";

/**
 * Contains the app-wide state of a ReusableDialog.
 */
export type DialogState = {
  /**
   * Whether or not the dialog should be open.
   */
  open: boolean;
};

export const dialogState = reactive<{
  [key: string]: DialogState;
}>({});
