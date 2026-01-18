import { computed, ComputedRef, inject, ref, watch } from "vue";
import { appState, datasource, elements } from "@/lib/appState";
import { FrontendConfig } from "@/lib/config";
import { toast } from "vue-sonner";
import { getTargetSize } from "@/components/image-viewer/api.ts";
import { SelectionAreaSelection, SelectionAreaType } from "@/lib/selection.ts";
import {
  areSelectionAreaSelectionsEqual,
  deepClone,
  flipSelectionAreaSelection,
  hasActiveSelection,
} from "@/lib/utils.ts";

/**
 * Status enum for tracking the state of asynchronous operations.
 */
export enum Status {
  WAITING,
  LOADING,
  ERROR,
  SUCCESS,
}

/**
 * Custom type for keeping track of what selection to use.
 */
export type ColorSegmentationAreaSelection = {
  /**
   * The current area selection made by the user.
   */
  areaSelection: SelectionAreaSelection;
  /**
   * Timestamp of when the area selection was last changed.
   */
  lastChangedTimestamp: number;
};

/**
 * Custom type for keeping track of what selection to use.
 */
export type ColorSegmentationRequestBody = {
  /**
   * The area selection to use.
   */
  selection: SelectionAreaSelection;
  /**
   * The elements and their thresholds to use.
   */
  elements: [number, number][];
};

/**
 * Type for segmentation mode.
 */
export type SegmentationMode = "complete" | "elements";

/**
 * Composable function for managing color segmentation window state and behavior.
 * @returns An object containing reactive state and methods for color segmentation.
 */
export function useCSWindow() {
  // Constants and injected values
  const recommendedStatus = ref(Status.WAITING);
  const config = inject<FrontendConfig>("config")!;
  const selection = computed(() => appState.selection.colorSegmentation);
  const number_clusters = ref(10);
  const currentError = ref("Unknown error");
  const colors = ref<string[]>([""]);
  const useSelectionChecked = ref<boolean>(false);
  const status = ref(Status.WAITING);
  const segmentationMode = ref<SegmentationMode>("complete");

  const elementsSelected = ref([{ id: 1, name: "", threshold: 20 }]);
  const selectableElementsList = computed(() => elements.value);
  const disabledElements = computed(() => {
    // Collect all currently selected names (except empty)
    return elementsSelected.value.map((e) => e.name).filter((name) => name);
  });

  // Computed properties
  const areaSelection: ComputedRef<SelectionAreaSelection> = computed(() => appState.selection.imageViewer);

  // Non-reactive variables
  const currentAreaSelection: ColorSegmentationAreaSelection = {
    areaSelection: {
      type: SelectionAreaType.Rectangle,
      points: [
        { x: 0, y: 0 },
        { x: 10000, y: 10000 },
      ],
    },
    lastChangedTimestamp: Date.now(),
  };

  // Watchers
  watch(areaSelection, updateAreaSelection, { deep: true, immediate: true });

  /**
   * Fetch the hexadecimal colors' data.
   * @returns True if the colors were fetched successfully, false otherwise.
   */
  async function fetchColors() {
    status.value = Status.LOADING;
    const selectedElements: [number, number][] = [];

    // Validate and Build Payload based on Mode
    if (segmentationMode.value === "elements") {
      // Validation: Must have at least one element selected
      if (elementsSelected.value.length === 0 || !elementsSelected.value[0].name) {
        currentError.value = "Please select at least one element";
        status.value = Status.ERROR;
        return false;
      }

      // Build payload for specific elements
      for (let i = 0; i < elementsSelected.value.length; i++) {
        if (elementsSelected.value[i].name) {
          selectedElements.push([getElementIndex(elementsSelected.value[i].name), elementsSelected.value[i].threshold]);
        }
      }
    } else {
      // Complete Painting Mode: Send index 0 (Complete)
      // Threshold doesn't matter for complete painting, sending 0
      selectedElements.push([0, 0]);
    }

    //Read the selection for the payload
    let activeSelection: SelectionAreaSelection;
    if (useSelectionChecked.value) {
      activeSelection = flipSelectionAreaSelection(currentAreaSelection.areaSelection, (await getTargetSize()).height);
    } else {
      activeSelection = await getFullImageSelection();
    }

    //Create payload json
    const request_body: ColorSegmentationRequestBody = {
      selection: activeSelection,
      elements: selectedElements,
    };

    //Perform request
    const response = await fetch(
      `${config.api.endpoint}/${datasource.value}/cs/clusters/` +
        `/${number_clusters.value}/${useSelectionChecked.value}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request_body),
      },
    );
    selection.value.lastColorSegmentationRun = Date.now();

    if (!response.ok) {
      toast.warning("Failed to retrieve colors");
      currentError.value = "Failed to retrieve or generate color clusters";
      status.value = Status.ERROR;
      return false;
    }

    colors.value = await response.json();
    return true;
  }

  /**
   * Generates color clusters based on the user-set parameters,
   * and updates the CS selection.
   */
  async function generateColors() {
    try {
      // Whether the colors were fetched properly
      await fetchColors();
    } catch (e) {
      status.value = Status.ERROR;
      toast.warning("Failed to retrieve painting colors");
      console.error("Error fetching colors data", e);
      return;
    }
    status.value = Status.SUCCESS;

    updateSelection();
  }

  /**
   * Sets the CS selection.
   */
  function updateSelection() {
    if (selection.value != undefined) {
      // Update selection
      selection.value.elements = [] as number[];
      selection.value.thresholds = [] as number[];

      if (segmentationMode.value === "elements") {
        for (let i = 0; i < elementsSelected.value.length; i++) {
          if (elementsSelected.value[i].name) {
            selection.value.elements.push(getElementIndex(elementsSelected.value[i].name));
            selection.value.thresholds.push(elementsSelected.value[i].threshold);
          }
        }
      } else {
        // Complete painting logic
        selection.value.elements.push(0);
        selection.value.thresholds.push(0);
      }

      selection.value.enabled = Array(colors.value.length).fill(false);
      selection.value.colors = colors.value;
      selection.value.k = number_clusters.value;

      selection.value.useAreaSelection = useSelectionChecked.value;
      selection.value.areaSelection = deepClone(currentAreaSelection.areaSelection);
      selection.value.lastCompleteSelectionTimestamp = currentAreaSelection.lastChangedTimestamp;
    }
  }

  /**
   * Updates the currentAreaSelection if the new Selection made by the user is a new one, and valid.
   * @param newSelection The new selection made by the user.
   */
  function updateAreaSelection(newSelection: SelectionAreaSelection) {
    if (
      hasActiveSelection(newSelection) &&
      !areSelectionAreaSelectionsEqual(newSelection, currentAreaSelection.areaSelection)
    ) {
      currentAreaSelection.areaSelection = deepClone(newSelection);
      currentAreaSelection.lastChangedTimestamp = Date.now();
    }
  }

  /**
   * Toggles (enables/disables) the given color cluster.
   * @param colorIndex The index of the selected cluster/color.
   */
  function toggleCluster(colorIndex: number) {
    if (selection.value.enabled[colorIndex] != undefined) {
      selection.value.enabled[colorIndex] = !selection.value.enabled[colorIndex];
    }
  }

  /**
   * Enables all color clusters.
   */
  function enableAllClusters() {
    for (let i = 0; i < selection.value.enabled.length; i++) {
      if (selection.value.enabled[i] != undefined) {
        selection.value.enabled[i] = true;
      }
    }
  }

  /**
   * Disables all color clusters.
   */
  function disableAllClusters() {
    for (let i = 0; i < selection.value.enabled.length; i++) {
      if (selection.value.enabled[i] != undefined) {
        selection.value.enabled[i] = false;
      }
    }
  }

  /**
   * Returns the index of the given element/complete painting to pass to the backend,
   * by setting the complete painting to index 0, and
   * the elements to their channel number plus 1.
   * @param elementName Name of element/complete painting to get index of.
   * @returns Index of the element/complete painting.
   */
  function getElementIndex(elementName: string | undefined) {
    if (elementName == undefined) {
      return 0;
    }
    // Get index of new channel
    const index = elements.value.findIndex((element) => element.name === elementName);
    return elements.value[index].channel + 1;
  }

  /**
   * Adds a new element item with default values into the list of elements. Is used when the
   * user presses the button "Add element".
   */
  const addElementSelection = () => {
    const newElement = {
      id: elementsSelected.value.length + 1,
      name: "",
      threshold: 20,
    };
    elementsSelected.value.push(newElement);
  };

  /**
   * Remove an element from the selected elements list.
   * @param index The index of the element in the list to be removed.
   */
  function removeElement(index: number) {
    // Only remove if there's more than 1 element in the list
    if (elementsSelected.value.length > 1) {
      elementsSelected.value.splice(index, 1);
    }
  }

  /**
   * Returns a selection object that exactly covers the entire painting.
   * @returns A `SelectionAreaSelection` object exactly covering the entire painting.
   */
  async function getFullImageSelection(): Promise<SelectionAreaSelection> {
    const size = await getTargetSize();
    return {
      type: SelectionAreaType.Rectangle,
      points: [
        { x: 0, y: 0 },
        { x: size.width, y: size.height },
      ],
    };
  }

  const recommendedClusters = ref<number | null>(null);

  /**
   * Calculates the recommended number of clusters based on the current element selection and area selection.
   */
  async function calculateRecommendedClusters() {
    try {
      const selectedElements: [number, number][] = [];

      // Build payload based on mode
      if (segmentationMode.value === "elements") {
        // Validation
        for (const sel of elementsSelected.value) {
          if (!sel || !sel.name || sel.threshold === undefined) {
            toast.error("Invalid element selection");
            return;
          }
        }
        // Build payload for specific elements
        for (const sel of elementsSelected.value) {
          if (sel.name) {
            selectedElements.push([getElementIndex(sel.name), sel.threshold]);
          }
        }
      } else {
        // Complete Painting Mode
        selectedElements.push([0, 0]);
      }

      recommendedStatus.value = Status.LOADING;

      //Read the selection for the payload
      const activeSelection: SelectionAreaSelection = await setActiveSelection();

      // Prepare request
      const response = await fetch(`${config.api.endpoint}/${datasource.value}/cs/recommend-k`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selection: activeSelection,
          elements: selectedElements,
        }),
      });
      // Handle response
      if (!response.ok) {
        recommendedStatus.value = Status.ERROR;
        toast.error("Failed to calculate recommended clusters");
        return;
      }
      // Get data
      const data = await response.json();
      recommendedClusters.value = data.recommended_k;
      recommendedStatus.value = Status.SUCCESS;
    } catch (err) {
      recommendedStatus.value = Status.ERROR;
      console.error(err);
      toast.error("Error calculating recommended clusters");
    }
  }

  /**
   * Helper function to get the active selection based on whether the selection checkbox is checked.
   * @returns - The active selection to be used.
   */
  async function setActiveSelection() {
    if (useSelectionChecked.value) {
      return flipSelectionAreaSelection(currentAreaSelection.areaSelection, (await getTargetSize()).height);
    } else {
      return await getFullImageSelection();
    }
  }

  /**
   * Reset all settings in the window to defaults.
   */
  function resetSettings() {
    recommendedStatus.value = Status.WAITING;
    recommendedClusters.value = null;
    number_clusters.value = 10;
    colors.value = [""];
    useSelectionChecked.value = false;
    status.value = Status.WAITING;
    elementsSelected.value = [{ id: 1, name: "", threshold: 20 }];
  }

  /**
   * Update number of clusters variable to match the calculated recommended number of clusters.
   */
  async function setRecommendedClusters() {
    if (recommendedClusters.value == null) {
      return;
    }
    number_clusters.value = recommendedClusters.value;
  }

  return {
    // Constants and injected values
    recommendedStatus,
    selection,
    number_clusters,
    currentError,
    colors,
    useSelectionChecked,
    status,
    segmentationMode,
    elementsSelected,
    selectableElementsList,
    disabledElements,
    recommendedClusters,

    // Methods
    generateColors,
    toggleCluster,
    enableAllClusters,
    disableAllClusters,
    addElementSelection,
    removeElement,
    calculateRecommendedClusters,
    setRecommendedClusters,
    resetSettings,
  };
}
