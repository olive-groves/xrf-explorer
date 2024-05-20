import { snakeCase } from "change-case";
import { dialogState } from "./state";

/**
 * Opens a dialog.
 * @param id The id of the dialog that should be opened.
 */
export function openDialog(id: string) {
  const formattedId = snakeCase(id);
  console.log(formattedId, dialogState);
  if (formattedId in dialogState) {
    dialogState[formattedId].open = true;
  } else {
    console.warn(
      `Attempted to open dialog with id ${id}, no such dialog exists. Known dialogs are [${Object.keys(dialogState)}].`,
    );
  }
}

/**
 * Closes a dialog.
 * @param id The id of the dialog that should be closed.
 */
export function closeDialog(id: string) {
  const formattedId = snakeCase(id);
  dialogState[formattedId].open = false;
}
