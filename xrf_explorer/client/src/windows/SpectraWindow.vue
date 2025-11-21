<script setup lang="ts">
import { computed, ComputedRef, inject, nextTick, ref, watch } from "vue";
import { FrontendConfig } from "@/lib/config";
import * as d3 from "d3";
import { appState, datasource, spectralDataPresent } from "@/lib/appState";
import { SelectionAreaSelection, SelectionAreaType } from "@/lib/selection";
import { exportableElements } from "@/lib/export";
import {
  NumberField,
  NumberFieldContent,
  NumberFieldDecrement,
  NumberFieldIncrement,
  NumberFieldInput,
} from "@/components/ui/number-field";
import { flipSelectionAreaSelection } from "@/lib/utils";
import { getTargetSize } from "@/components/image-viewer/api";
import { LoaderPinwheel, Maximize2, RotateCcw } from "lucide-vue-next";
import { Button } from "@/components/ui/button";
import { makeSpectraChart } from "./charts";
import { toast } from "vue-sonner";
import { Dialog, DialogTrigger, DialogContent, DialogTitle } from "@/components/ui/dialog";
import PeriodicTable from "./PeriodicTable.vue";

const spectraChart = ref<HTMLElement>();
const popupSpectraChart = ref<HTMLElement>();
const popupVisible = ref(false);
let ready: boolean = false;

const binningData = ref(false);
const loadingSelection = ref(false);
const loadingGlobal = ref(false);



// Zoom State
let currentZoomTransform: d3.ZoomTransform | null = null;

// Area selection
const areaSelection: ComputedRef<SelectionAreaSelection> = computed(() => appState.selection.imageViewer);
watch(areaSelection, getSelectionSpectrum, { deep: true, immediate: true });

/**
 * Sets up export of chart.
 */
watch(spectraChart, (value) => (exportableElements["Spectral"] = value), { immediate: true });

// Binning parameters
const low = computed(() => appState.workspace?.spectralParams?.low ?? 0);
const high = computed(() => appState.workspace?.spectralParams?.high ?? 4096);
const binSize = computed(() => appState.workspace?.spectralParams?.binSize ?? 1);
const binned = computed(() => appState.workspace?.spectralParams?.binned ?? false);

let abortController = new AbortController();

const config = inject<FrontendConfig>("config")!;

// set the dimensions and margins of the graph
const margin = { top: 30, right: 30, bottom: 70, left: 60 },
  width = 860 - margin.left - margin.right,
  height = 600 - margin.top - margin.bottom;

// For all variables below, index is bin/channel number, and value is average intensity for that bin/channel
// Points of the global average spectrum
let globalData: number[] = [];
// Points of the selected average spectrum
let selectionData: number[] = [];
// Points of the theoretical element spectrum
let elementData: number[] = [];
// Coordinates of the theoretical element peaks
let elementPeaks: number[] = [];
// X-axis offset
let offset: number = 0;

/**
 * Set up the svg and axis of the graph.
 */
async function setup() {
  ready = binned.value;
  binningData.value = !ready;
  watch(binned, () => {
    ready = binned.value;
    binningData.value = !ready;
    if (globalData.length == 0) {
      getAverageSpectrum();
    }
  });
  offset = await getOffset();
  await getAverageSpectrum();
  drawChart();
}

/**
 * Fetches the x-axis offset of the spectra.
 * @returns - The offset.
 */
async function getOffset() {
  try {
    //make api call
    const response = await fetch(`${config.api.endpoint}/${datasource.value}/get_offset`);
    return await response.json();
  } catch (e) {
    console.error("Error getting energy offset", e);
    return 0;
  }
}

/**
 * Set up the axis and plot the data.
 */
/**
 * Set up the axis and plot the data.
 */
function drawChart() {
  const target = popupVisible.value ? popupSpectraChart.value : spectraChart.value;
  if (!target) return;

  makeSpectraChart(
    target,
    {
      global: globalData,
      selection: selectionData,
      element: elementData,
      elementPeaks: elementPeaks,
    },
    {
      low: low.value,
      high: high.value,
      binSize: binSize.value,
      offset: offset,
    },
    {
      globalChecked: globalChecked.value,
      selectionChecked: selectionChecked.value,
      elementChecked: elementChecked.value,
      selectedElement: selectedElement.value,
    },
    {
      width: width,
      height: height,
      margin: margin,
    },
    {
      currentZoomTransform: currentZoomTransform,
      setZoomTransform: (t) => (currentZoomTransform = t),
    },
  );
}

const globalChecked = ref(false);
const elementChecked = ref(false);
const selectionChecked = ref(false);
const selectedElement = ref("No element");
const excitation = ref(0);



/**
 * Plots the average channel spectrum over the whole painting in the chart.
 */
async function getAverageSpectrum() {
  if (ready) {
    loadingGlobal.value = true;
    try {
      const size = await getTargetSize();
      const request_body: SelectionAreaSelection = {
        type: SelectionAreaType.Rectangle,
        points: [
          { x: 0, y: 0 },
          { x: size.width, y: size.height },
        ],
      };
      //make api call
      const response = await fetch(`${config.api.endpoint}/${datasource.value}/get_selection_spectrum`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request_body),
      });
      globalData = await response.json();
      drawChart();
    } catch (e) {
      toast.warning("Something went wrong while fetching spectrum data.");
      console.error("Error getting global average spectrum", e);
    }
    loadingGlobal.value = false;
  }
}

/**
 * Plots the average graph of the given pixels.
 * For now assumes that the pixels are given in the raw data coordinate system.
 * @param selection Json object representing the selection.
 */
async function getSelectionSpectrum(selection: SelectionAreaSelection) {
  if (ready && selectionChecked.value) {
    // Abort any previous requests
    abortController.abort();
    abortController = new AbortController();
    loadingSelection.value = true;

    // clear selection
    if (selection.type == undefined) selectionData = [];
    // update new selection
    else {
      // Request body for selection
      const request_body = flipSelectionAreaSelection(selection, (await getTargetSize()).height);

      try {
        //make api call
        const response = await fetch(`${config.api.endpoint}/${datasource.value}/get_selection_spectrum`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request_body),
          signal: abortController.signal,
        });
        selectionData = await response.json();
      } catch (e) {
        console.error("Error getting selection average spectrum", e);
      }
    }

    // update plot
    drawChart();
    loadingSelection.value = false;
  }
}

/**
 * Plots the theoretical spectrum and peaks of an element.
 * @param element Symbol of element to be plotted.
 * @param excitation Excitation energy.
 */
async function getElementSpectrum(element: string, excitation: number) {
  if (element != "No element" && element != "" && excitation != null && (excitation as unknown as string) != "") {
    try {
      //make api call
      const response = await fetch(
        `${config.api.endpoint}/${datasource.value}/get_element_spectrum/${element}/${excitation}`,
      );
      const data = await response.json();
      elementData = data[0];
      elementPeaks = data[1];
      drawChart();
    } catch (e) {
      console.error("Error getting element theoretical spectrum", e);
      elementData = [];
      elementPeaks = [];
      drawChart();
    }
  } else {
    elementData = [];
    elementPeaks = [];
    drawChart();
  }
}



/**
 * Plots element spectrum when an element is selected in the dropdown.
 */
function updateElementSpectrum() {
  getElementSpectrum(selectedElement.value, excitation.value);
}

watch(popupVisible, async () => {
  await nextTick();
  drawChart();
});

function resetZoom() {
  currentZoomTransform = null;
  drawChart();
}
</script>

<template>
  <Window title="Spectrum" location="right" @window-mounted="setup" :disabled="!spectralDataPresent">
    <div class="mx-2">
      <!-- SPECTRA SELECTION -->
      <div class="space-y-1">
        <p class="font-bold">Select which spectra to show:</p>
        <div class="mt-1 flex items-center">
          <Checkbox id="globalCheck" v-model:checked="globalChecked" @update:checked="drawChart" />
          <label class="ml-1" for="globalCheck">Global average</label>
        </div>
        <div class="mt-1 flex items-center">
          <Checkbox id="selectionCheck" v-model:checked="selectionChecked" @update:checked="drawChart" />
          <label class="ml-1" for="selectionCheck">Selection average</label>
        </div>
        <div class="mt-1 flex items-center">
          <Checkbox id="elementCheck" v-model:checked="elementChecked" @update:checked="drawChart" />
          <label class="ml-1" for="elementCheck">Element theoretical</label>
        </div>
      </div>
      <!-- ELEMENT SELECTION -->
      <Separator class="mt-2" />
      <p class="ml-1 font-bold">Theoretical spectrum properties:</p>
      <div class="flex-1 space-y-1">
        <Label for="element">Element</Label>
        <div class="ml-1 mt-2">
          <PeriodicTable v-model="selectedElement" @select="updateElementSpectrum" />
        </div>
      </div>
      <div class="flex-1 space-y-1">
        <Label for="excitation-input">Excitation level (keV)</Label>
        <NumberField
          id="excitation-input"
          class="ml-1 mt-1 max-w-[200px]"
          v-model="excitation"
          @update:model-value="updateElementSpectrum"
          :min="0"
          :max="40"
        >
          <NumberFieldContent>
            <NumberFieldInput />
            <NumberFieldDecrement />
            <NumberFieldIncrement />
          </NumberFieldContent>
        </NumberField>
      </div>
      <!-- PLOTTING THE CHART -->
      <Separator class="mt-2" />
      <p class="ml-1 font-bold">Generated spectra chart:</p>
      <div class="relative">
        <svg class="ml-1" ref="spectraChart"></svg>
        <div
          v-if="loadingGlobal || loadingSelection || binningData"
          class="absolute left-0 top-0 flex size-full items-center justify-center bg-muted/30"
        >
          <div class="size-6">
            <LoaderPinwheel class="size-full animate-spin" />
          </div>
        </div>
        <div class="mt-2 mb-2 flex gap-2">
          <Button variant="outline" size="icon" @click="popupVisible = true" title="Open Popup Spectra Chart">
            <Maximize2 class="size-4" />
          </Button>
          <Button variant="outline" size="icon" @click="resetZoom" title="Reset Zoom">
            <RotateCcw class="size-4" />
          </Button>
        </div>
      </div>

      <!-- Popup Spectra Chart -->
      <Dialog v-model:open="popupVisible">
        <DialogTrigger as-child>
          <span></span>
        </DialogTrigger>

        <DialogContent class="fixed left-1/2 top-1/2 w-[950px] max-w-[95vw] -translate-x-1/2 -translate-y-1/2 p-6">
          <DialogTitle>Spectra Chart</DialogTitle>
          <div class="mt-4 flex justify-center">
            <svg ref="popupSpectraChart" width="900" height="600"></svg>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  </Window>
</template>
