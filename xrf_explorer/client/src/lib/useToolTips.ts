import tooltips from "../tooltips.json";

/**
 * The tooltip tree from the json.
 */
export type TooltipTree = typeof tooltips;

/**
 * Recursively resolve "editor.save" → tooltips.editor.save.
 * @param key The key to get the tooltip from.
 * @returns String containing the tooltip.
 */
export function getTooltipByKey(key: string): string {
  const parts = key.split(".");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let current: any = tooltips;

  for (const part of parts) {
    current = current?.[part];
    if (!current) return "";
  }

  console.log("Tooltip " + key + " is: " + current);

  return current;
}
