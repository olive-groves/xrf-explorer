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

  const elementsSelected = ref([{ id: 1, name: "", threshold: 20 }]);
  const selectableElementsList = computed(() => elements.value);
  const disabledElements = computed(() => {
    // Collect all currently selected names (except empty and 'complete')
    return elementsSelected.value.map((e) => e.name).filter((name) => name && name !== "complete");
  });

  // Dialog visibility ref for confirmation
  const showConfirmDialog = ref(false);
  let pendingElementsSelected: typeof elementsSelected.value | null = null;

  /**
   * Function to handle the user's choice in the confirmation dialog.
   * @param choice User's choice: true for confirm, false for cancel.
   */
  function handleConfirm(choice: boolean) {
    if (choice) {
      elementsSelected.value = [{ id: 1, name: "complete", threshold: elementsSelected.value[0].threshold }];
    } else {
      if (pendingElementsSelected) {
        const firstNonComplete = pendingElementsSelected.find((sel) => sel.name && sel.name !== "complete");
        if (firstNonComplete) {
          elementsSelected.value = [firstNonComplete];
        } else {
          elementsSelected.value = pendingElementsSelected.map((e) => (e.name === "complete" ? { ...e, name: "" } : e));
        }
      }
    }
    pendingElementsSelected = null;
    showConfirmDialog.value = false;
  }

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

  // Watch for selection of "complete" with other elements, and confirm with user
  watch(
    elementsSelected,
    (newVal) => {
      const hasComplete = newVal.some((sel) => sel.name === "complete");
      const hasOtherElements = newVal.some((sel) => sel.name && sel.name !== "" && sel.name !== "complete");

      if (hasComplete && hasOtherElements) {
        // Open dialog instead of window.confirm
        pendingElementsSelected = [...newVal];
        showConfirmDialog.value = true;
      }
    },
    { deep: true },
  );

  /**
   * Fetch the hexadecimal colors' data.
   * @returns True if the colors were fetched successfully, false otherwise.
   */
  async function fetchColors() {
    status.value = Status.LOADING;
    if (elementsSelected.value[0] == null) {
      currentError.value = "Please select an element";
      status.value = Status.ERROR;
      return;
    }

    //Read the selection for the payload
    let activeSelection: SelectionAreaSelection;
    if (useSelectionChecked.value) {
      activeSelection = flipSelectionAreaSelection(currentAreaSelection.areaSelection, (await getTargetSize()).height);
    } else {
      activeSelection = await getFullImageSelection();
    }

    //Read the elements for the payload
    const selectedElements: [number, number][] = [];
    for (let i = 0; i < elementsSelected.value.length; i++) {
      selectedElements.push([getElementIndex(elementsSelected.value[i].name), elementsSelected.value[i].threshold]);
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
      for (let i = 0; i < elementsSelected.value.length; i++) {
        selection.value.elements.push(getElementIndex(elementsSelected.value[i].name));
        selection.value.thresholds.push(elementsSelected.value[i].threshold);
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
    if (elementName == "complete") {
      return 0;
    } else {
      const index = elements.value.findIndex((element) => element.name === elementName);
      return elements.value[index].channel + 1;
    }
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
      // Catch when the user hasn't selected an element.
      for (const sel of elementsSelected.value) {
        if (!sel || !sel.name || sel.threshold === undefined) {
          toast.error("Invalid element selection");
          return;
        }
      }

      recommendedStatus.value = Status.LOADING;
      // Prepare request
      const response = await fetch(`${config.api.endpoint}/${datasource.value}/cs/recommend-k`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selection: flipSelectionAreaSelection(currentAreaSelection.areaSelection, (await getTargetSize()).height),
          elements: elementsSelected.value.map((sel) => [getElementIndex(sel.name), sel.threshold]),
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
    // config,
    selection,
    number_clusters,
    currentError,
    colors,
    useSelectionChecked,
    status,
    elementsSelected,
    selectableElementsList,
    disabledElements,
    showConfirmDialog,
    recommendedClusters,

    // Methods
    handleConfirm,
    generateColors,
    toggleCluster,
    enableAllClusters,
    disableAllClusters,
    addElementSelection,
    removeElement,
    calculateRecommendedClusters,
    setRecommendedClusters,
  };
}
