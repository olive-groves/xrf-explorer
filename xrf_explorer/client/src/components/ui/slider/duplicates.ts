import { LayerGroup, LayerVisibility } from "@/components/image-viewer/types";
import { type Ref, watch } from "vue";

/**
 * Toggles the pinned state of a LayerGroup.
 * @param group - The LayerGroup to toggle the pinned state for.
 * @param numberofPinnedLayers - The current number of pinned layers.
 * @returns An object indicating the new pinned state of the group.
 */
export function togglePin(group: LayerGroup, numberofPinnedLayers: number): boolean {
  if (!group.pinned) {
    // Try to pin the group
    if (numberofPinnedLayers >= 3) {
      alert("You can only pin up to 3 layers.");
      return group.pinned;
    }
    group.pinned = true;
  } else {
    // Unpin the group
    group.pinned = false;
  }
  return group.pinned;
}

/**
 * Updates the visibility of the layer group outside the lens.
 * @param LayerVisibility - The LayerVisibility enum.
 * @param group - The group to toggle and update.
 */
export function checkedOutsideLens(group: LayerGroup) {
  if (group.visibility == LayerVisibility.Invisible) {
    group.visibility = LayerVisibility.OutsideLens;
  } else if (group.visibility == LayerVisibility.Visible) {
    group.visibility = LayerVisibility.InsideLens;
  } else if (group.visibility == LayerVisibility.InsideLens) {
    group.visibility = LayerVisibility.Visible;
  } else if (group.visibility == LayerVisibility.OutsideLens) {
    group.visibility = LayerVisibility.Invisible;
  }
}
/**
 * Interface representing a property for the slider component.
 */
export interface Property {
  /** The display name of the property. */
  name: string;
  /** The minimum value for the slider. */
  min: number;
  /** The maximum value for the slider. */
  max: number;
  /** The default value for the slider. */
  default: number;
  /** The name of the property in the LayerGroup. */
  propertyName: string;
  /** The key reference to the property in the LayerGroup. */
  nameRef: keyof LayerGroup;
}

// Adjustable properties of each layer group.
// Main properties are always directly visible in the Layer System,
// all other properties are placed in a separate popover.
export const mainProperties = ["Opacity"];
export const properties: Property[] = [
  { name: "Opacity", min: 0, max: 1, default: 1, propertyName: "opacityProperty", nameRef: "opacity" },
  { name: "Contrast", min: 0, max: 5, default: 1, propertyName: "contrastProperty", nameRef: "contrast" },
  { name: "Saturation", min: 0, max: 5, default: 1, propertyName: "saturationProperty", nameRef: "saturation" },
  { name: "Gamma", min: 0, max: 5, default: 1, propertyName: "gammaProperty", nameRef: "gamma" },
  { name: "Brightness", min: -1, max: 1, default: 0, propertyName: "brightnessProperty", nameRef: "brightness" },
];



/**
 * Watchers for LayerGroup properties.
 * @param groupNames - A Ref containing the names of the layer groups.
 * @param layerGroups - A Ref containing a mapping of layer group names to LayerGroup objects.
 * @param groups - A Ref containing the array of LayerGroup objects.
 * @param setLayerGroupIndex - A function to update the index of a LayerGroup.
 */
export function watchers(
  groupNames: Ref<string[]>,
  layerGroups: Ref<{ [key: string]: LayerGroup }>,
  groups: Ref<LayerGroup[]>,
  setLayerGroupIndex: (group: LayerGroup) => void,
) {
  /**
   * Loads the layer groups into the LayerSystem.
   */
  watch(
    groupNames,
    (newGroups) => {
      groups.value = newGroups.map((name) => layerGroups.value[name]).sort((a, b) => a.index - b.index);
    },
    { immediate: true },
  );

  /**
   * Updates the indices of the layers when the layers get reordered.
   */
  watch(
    groups,
    (newOrder) => {
      newOrder.forEach((layer, index) => {
        layer.index = index;
        setLayerGroupIndex(layer);
      });
    },
    { immediate: true },
  );
}
