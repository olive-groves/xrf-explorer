<script setup lang="ts">
import { computed, ComputedRef, inject, nextTick, ref, watch } from "vue";
import { FrontendConfig } from "@/lib/config";
import * as d3 from "d3";
import { appState, datasource, spectralDataPresent } from "@/lib/appState";
import { SelectionAreaSelection, SelectionAreaType } from "@/lib/selection";
import { exportableElements } from "@/lib/export";
import { ELEMENT_SYMBOLS, ELEMENT_NO_SPECTRAL_DATA } from "./elementSymbols";
import {
  NumberField,
  NumberFieldContent,
  NumberFieldDecrement,
  NumberFieldIncrement,
  NumberFieldInput,
} from "@/components/ui/number-field";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { flipSelectionAreaSelection } from "@/lib/utils";
import { getTargetSize } from "@/components/image-viewer/api";
import { LoaderPinwheel } from "lucide-vue-next";
import { clearChart } from "./charts";
import { toast } from "vue-sonner";
import { Dialog, DialogTrigger, DialogContent, DialogTitle } from "@/components/ui/dialog";

const spectraChart = ref<HTMLElement>();
const popupSpectraChart = ref<HTMLElement>();
const popupVisible = ref(false);
let ready: boolean = false;

const binningData = ref(false);
const loadingSelection = ref(false);
const loadingGlobal = ref(false);

// Popover state for element selection
const popoverOpen = ref(false);

// SVG container
let svg = d3.select(spectraChart.value!); // Default selection
let x = d3.scaleLinear();
let y = d3.scaleLinear();

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

// Periodic table layout (element indices, null for empty spaces). IUPAC format.
const periodicTableLayout = [
  [1, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, 2],
  [3, 4, null, null, null, null, null, null, null, null, null, null, 5, 6, 7, 8, 9, 10],
  [11, 12, null, null, null, null, null, null, null, null, null, null, 13, 14, 15, 16, 17, 18],
  [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],
  [37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54],
  [55, 56, null, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86],
  [87, 88, null, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118],
  [null, null, null, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71],
  [null, null, null, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103],
];

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
  makeChart();
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
function makeChart() {
  const target = popupVisible.value ? popupSpectraChart : spectraChart;

  clearChart(svg);

  // Block viewing graphs below x-axis and left of y-axis
  svg
    .append("defs")
    .append("clipPath")
    .attr("id", "chart-area-clip")
    .append("rect")
    .attr("x", margin.left)
    .attr("y", margin.top)
    .attr("width", width - margin.left - margin.right)
    .attr("height", height - margin.top - margin.bottom);

  const max = getMax();

  // Add X and Y axis
  x = d3
    .scaleLinear()
    .range([margin.left, width - margin.right])
    .domain([low.value * ((40 - offset) / high.value) + offset, high.value * ((40 - offset) / high.value) + offset]);
  y = d3
    .scaleLinear()
    .range([height - margin.bottom, margin.top])
    .domain([0, max * (100 / 255)]);

  // append the svg object to the body of the page
  svg = d3
    .select(target.value!)
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto;");

  // add axis
  svg
    .append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0, ${height - margin.bottom})`)
    .call(d3.axisBottom(x))
    .call((g) =>
      g
        .append("text")
        .attr("x", width / 2)
        .attr("y", 50)
        .attr("fill", "currentColor")
        .attr("text-anchor", "start")
        .text("Energy (keV)"),
    );

  svg
    .append("g")
    .attr("class", "y-axis")
    .attr("transform", `translate(${margin.left}, 0)`)
    .call(d3.axisLeft(y))
    .call((g) =>
      g
        .append("text")
        .attr("x", -margin.left)
        .attr("y", 20)
        .attr("fill", "currentColor")
        .attr("text-anchor", "start")
        .text("Count (%)"),
    );

  // Create a group for the plot area and apply the clip-path
  const plotArea = svg.append("g").attr("clip-path", "url(#chart-area-clip)");

  // create line
  const globalLine = createLine();

  // Add the line to chart
  plotArea
    .append("path")
    .datum(globalData)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 1)
    .attr("id", "globalLine")
    .attr("d", globalLine)
    .style("opacity", 0);

  // modify visibility based on checkbox status
  updateGlobal();

  // remove spectrum of previous selection
  svg.select("#selectionLine").remove();

  // create line
  const selectionLine = createLine();

  // Add the line to chart
  plotArea
    .append("path")
    .datum(selectionData)
    .attr("fill", "none")
    .attr("stroke", "green")
    .attr("stroke-width", 1)
    .attr("id", "selectionLine")
    .attr("d", selectionLine)
    .style("opacity", 0);

  // modify visibility based on checkbox status
  updateSelectionSpectrum();

  // remove previous element lines
  svg.select("#elementLine").remove();
  svg.selectAll(".peak-line").remove();

  // create line
  const elementLine = createLine();

  // Add the line to chart
  plotArea
    .append("path")
    .datum(elementData)
    .attr("fill", "none")
    .attr("stroke", "orange")
    .attr("stroke-width", 1)
    .attr("id", "elementLine")
    .attr("d", elementLine)
    .style("opacity", 0);

  //Add peaks
  elementPeaks.forEach((index) => {
    plotArea
      .append("line")
      .attr("class", "peak-line")
      .style("stroke", "grey")
      .style("stroke-width", 1)
      .attr("x1", x((index * binSize.value + low.value) * ((40 - offset) / high.value) + offset))
      .attr("y1", 30)
      .attr("x2", x((index * binSize.value + low.value) * ((40 - offset) / high.value) + offset))
      .attr("y2", 430);
  });

  // modify visibility based on checkbox status
  updateElement();

  const zoom = d3
    .zoom()
    .scaleExtent([1, 8])
    .on("zoom", (event) => {
      currentZoomTransform = event.transform; // Store the current transform
      const newX = event.transform.rescaleX(x);
      const newY = event.transform.rescaleY(y);

      // Update axes
      svg.select(".x-axis").call(d3.axisBottom(newX) as never);
      svg.select(".y-axis").call(d3.axisLeft(newY) as never);

      // Create new line generator with transformed scales
      const zoomedLine = d3
        .line<number>()
        .x((_, i) => newX((i * binSize.value + low.value) * ((40 - offset) / high.value) + offset))
        .y((d) => newY(d * (100 / 255)));

      // Update all lines with zoomed scales
      svg.select("#globalLine").attr("d", zoomedLine(globalData));
      svg.select("#selectionLine").attr("d", zoomedLine(selectionData));
      svg.select("#elementLine").attr("d", zoomedLine(elementData));

      // Update peaks
      svg
        .selectAll(".peak-line")
        .attr("x1", (_, i) =>
          newX((elementPeaks[i] * binSize.value + low.value) * ((40 - offset) / high.value) + offset),
        )
        .attr("x2", (_, i) =>
          newX((elementPeaks[i] * binSize.value + low.value) * ((40 - offset) / high.value) + offset),
        );
    });

  svg.call(zoom as never);

  // Restore the previous zoom transform if it exists
  if (currentZoomTransform) {
    svg.call(zoom.transform as never, currentZoomTransform);
  }
}

const globalChecked = ref(false);
const elementChecked = ref(false);
const selectionChecked = ref(false);
const selectedElement = ref("No element");
const excitation = ref(0);

/**
 * Generates a D3 line based on the current binning parameters.
 * @returns - The D3 line.
 */
function createLine() {
  return d3
    .line<number>()
    .x((_, i) => x((i * binSize.value + low.value) * ((40 - offset) / high.value) + offset))
    .y((d, _) => y(d * (100 / 255)));
}

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
      makeChart();
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
    makeChart();
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
      makeChart();
    } catch (e) {
      console.error("Error getting element theoretical spectrum", e);
    }
  } else {
    // remove previous element line
    svg.select("#elementLine").remove();
    svg.selectAll(".peak-line").remove();
  }

  // modify visibility based on checkbox status
  updateElement();
}

/**
 * Get the maximum y-value of the current global and selected data.
 * @returns - The maximum y-value.
 */
function getMax() {
  let globalMax: number = d3.max(globalData, (d) => d) as number;
  let selectionMax: number = d3.max(selectionData, (d) => d) as number;

  // Initialize max values if they are NaN
  if (isNaN(globalMax)) globalMax = 0;
  if (isNaN(selectionMax)) selectionMax = 0;

  let max: number;

  // Update the global and selection max values
  if (selectionChecked.value && !globalChecked.value) {
    max = selectionMax;
  } else if (globalChecked.value && !selectionChecked.value) {
    max = globalMax;
  } else {
    max = Math.max(...[globalMax, selectionMax]);
  }

  return max;
}

/**
 * Updates visibility of global average spectrum.
 */
function updateGlobal() {
  if (globalChecked.value) {
    svg.select("#globalLine").style("opacity", 1);
  } else {
    svg.select("#globalLine").style("opacity", 0);
  }
}

/**
 * Updates visibility of element theoretical spectrum.
 */
function updateElement() {
  if (elementChecked.value && selectedElement.value != "No element") {
    svg.select("#elementLine").style("opacity", 1);
  } else {
    svg.select("#elementLine").style("opacity", 0);
  }
  if (selectedElement.value == "No element") {
    svg.selectAll(".peak-line").style("opacity", 0);
  } else {
    svg.selectAll(".peak-line").style("opacity", 1);
  }
}

/**
 * Updates visibility of selection average spectrum.
 */
function updateSelectionSpectrum() {
  if (selectionChecked.value) {
    svg.select("#selectionLine").style("opacity", 1);
  } else {
    svg.select("#selectionLine").style("opacity", 0);
  }
}

/**
 * Plots element spectrum when an element is selected in the dropdown.
 */
function updateElementSpectrum() {
  getElementSpectrum(selectedElement.value, excitation.value);
}

watch(popupVisible, async (open) => {
  await nextTick();
  svg = d3.select(open ? popupSpectraChart.value! : spectraChart.value!);
  makeChart();
});
</script>

<template>
  <Window title="Spectrum" location="right" @window-mounted="setup" :disabled="!spectralDataPresent">
    <div class="mx-2">
      <!-- SPECTRA SELECTION -->
      <div class="space-y-1">
        <p class="font-bold">Select which spectra to show:</p>
        <div class="mt-1 flex items-center">
          <Checkbox id="globalCheck" v-model:checked="globalChecked" @update:checked="makeChart" />
          <label class="ml-1" for="globalCheck">Global average</label>
        </div>
        <div class="mt-1 flex items-center">
          <Checkbox id="selectionCheck" v-model:checked="selectionChecked" @update:checked="makeChart" />
          <label class="ml-1" for="selectionCheck">Selection average</label>
        </div>
        <div class="mt-1 flex items-center">
          <Checkbox id="elementCheck" v-model:checked="elementChecked" @update:checked="makeChart" />
          <label class="ml-1" for="elementCheck">Element theoretical</label>
        </div>
      </div>
      <!-- ELEMENT SELECTION -->
      <Separator class="mt-2" />
      <p class="ml-1 font-bold">Choose element for theoretical spectrum:</p>
      <div class="ml-1 mt-2">
        <Popover v-model:open="popoverOpen">
          <PopoverTrigger as-child>
            <button
              class="inline-flex h-9 w-fit items-center justify-between rounded-md border border-input bg-background
                px-3 py-2 text-sm shadow-sm hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2
                focus:ring-ring"
            >
              <span>{{ selectedElement }}</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="ml-2 size-4 opacity-50"
              >
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>
          </PopoverTrigger>
          <PopoverContent class="w-auto p-3" align="start">
            <div class="overflow-x-auto">
              <div class="inline-grid gap-0.5" style="grid-template-columns: repeat(18, minmax(0, 1fr))">
                <template v-for="(row, rowIndex) in periodicTableLayout" :key="rowIndex">
                  <!-- Add an empty row between the main part and the extention -->
                  <div v-if="rowIndex === 7" class="col-span-full h-2"></div>

                  <template v-for="(elementIndex, colIndex) in row" :key="`${rowIndex}-${colIndex}`">
                    <div
                      v-if="rowIndex === 5 && colIndex === 2"
                      class="flex size-8 cursor-default items-center justify-center rounded border border-border
                        bg-red-500/30 text-[0.6rem] font-semibold text-foreground"
                    >
                      57-71
                    </div>

                    <div
                      v-else-if="rowIndex === 6 && colIndex === 2"
                      class="flex size-8 cursor-default items-center justify-center rounded border border-border
                        bg-red-500/60 text-[0.6rem] font-semibold text-foreground"
                    >
                      89-103
                    </div>

                    <button
                      v-else-if="elementIndex !== null && ELEMENT_SYMBOLS[elementIndex - 1]"
                      :disabled="ELEMENT_NO_SPECTRAL_DATA.includes(elementIndex)"
                      @click="
                        selectedElement = ELEMENT_SYMBOLS[elementIndex - 1];
                        updateElementSpectrum();
                        popoverOpen = false;
                      "
                      :class="[
                        'size-8 rounded border text-xs font-semibold transition-colors',
                        ELEMENT_NO_SPECTRAL_DATA.includes(elementIndex)
                          ? 'cursor-not-allowed border-secondary bg-secondary/50 text-muted-foreground'
                          : selectedElement === ELEMENT_SYMBOLS[elementIndex - 1]
                            ? 'border-primary bg-primary text-primary-foreground'
                            : rowIndex === 7
                              ? 'border-border bg-red-500/30 hover:bg-red-500/40'
                              : rowIndex === 8
                                ? 'border-border bg-red-500/60 hover:bg-red-500/70'
                                : 'border-border bg-secondary hover:bg-secondary/50',
                      ]"
                      :title="ELEMENT_SYMBOLS[elementIndex - 1]"
                    >
                      <div class="flex h-full flex-col items-center justify-center gap-0 leading-none">
                        <span class="my-0 text-[0.6rem] leading-none">{{ elementIndex }}</span>
                        <span class="my-0 leading-none">{{ ELEMENT_SYMBOLS[elementIndex - 1] }}</span>
                      </div>
                    </button>

                    <div v-else class="size-8"></div>
                  </template>
                </template>
              </div>
              <div class="my-2 flex h-full flex-col items-center justify-center">
                <span class="opacity-70">Greyed-out elements have no available theoretical data</span>
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </div>
      <!-- ENERGY SELECTION -->
      <Separator class="mt-2" />
      <p class="ml-1 mt-1 font-bold">Choose the excitation energy (keV):</p>
      <NumberField
        id="excitation-input"
        class="ml-1 mt-1 w-64"
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
        <button
          class="rounded-md border border-foreground bg-background px-3 py-1.5 font-medium text-foreground
            transition-colors hover:bg-foreground hover:text-background"
          @click="popupVisible = true"
        >
          Open Popup Spectra Chart
        </button>
      </div>

      <!-- Popup Spectra Chart -->
      <Dialog v-model:open="popupVisible">
        <DialogTrigger as-child>
          <span></span>
        </DialogTrigger>

        <DialogContent class="fixed left-1/2 top-1/2 w-[950px] max-w-[95vw] -translate-x-1/2 -translate-y-1/2 p-6">
          <DialogTitle>Spectra Chart (Popup)</DialogTitle>
          <div class="mt-4 flex justify-center">
            <svg ref="popupSpectraChart" width="900" height="600"></svg>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  </Window>
</template>
