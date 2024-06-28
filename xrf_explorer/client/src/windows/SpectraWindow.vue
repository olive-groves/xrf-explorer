<script setup lang="ts">
import { computed, ComputedRef, inject, ref, watch } from "vue";
import { FrontendConfig } from "@/lib/config";
import * as d3 from "d3";
import { appState, datasource, elements, spectralDataPresent } from "@/lib/appState";
import { ElementalChannel } from "@/lib/workspace";
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
import { LoaderPinwheel } from "lucide-vue-next";

const spectraChart = ref<HTMLElement>();
let ready: boolean = false;

const binningData = ref(false);
const loadingSelection = ref(false);
const loadingGlobal = ref(false);

// SVG container
let svg = d3.select(spectraChart.value!);
let x = d3.scaleLinear();
let y = d3.scaleLinear();

// Area selection
const areaSelection: ComputedRef<SelectionAreaSelection> = computed(() => appState.selection.imageViewer);
watch(areaSelection, getSelectionSpectrum, { deep: true, immediate: true });

/**
 * Sets up export of chart.
 */
watch(spectraChart, (value) => (exportableElements["Spectral"] = value), { immediate: true });

// Binning parameters
const high = computed(() => appState.workspace?.spectralParams?.high ?? 40);
const binSize = computed(() => appState.workspace?.spectralParams?.binSize ?? 1);
const binned = computed(() => appState.workspace?.spectralParams?.binned ?? false);
const low = computed(() => appState.workspace?.spectralParams?.low ?? 0);

let abortController = new AbortController();

const config = inject<FrontendConfig>("config")!;

// set the dimensions and margins of the graph
const margin = { top: 30, right: 30, bottom: 70, left: 60 },
  width = 860 - margin.left - margin.right,
  height = 600 - margin.top - margin.bottom;

const trimmedList: ComputedRef<ElementalChannel[]> = computed(() =>
  elements.value.filter((element: ElementalChannel) => element.name != "Continuum" && element.name != "chisq"),
);

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
 * Setup the svg and axis of the graph.
 */
async function setup() {
  trimmedList.value.unshift({ name: "No element", channel: -1, enabled: false });
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
    const offset = await response.json();
    return offset;
  } catch (e) {
    console.error("Error getting energy offset", e);
    return 0;
  }
}

/**
 * Clear the whole chart (including axes).
 */
function clearChart() {
  svg.selectAll("*").remove();
}

/**
 * Set up the axis and plot the data.
 */
function makeChart() {
  clearChart();

  const max = getMax();
  // Add X and Y axis
  x = d3
    .scaleLinear()
    .range([margin.left, width - margin.right])
    .domain([low.value * ((40 - offset) / 4096) + offset, high.value * ((40 - offset) / 4096) + offset]);
  y = d3
    .scaleLinear()
    .range([height - margin.bottom, margin.top])
    .domain([0, max * (100 / 255)]);

  // append the svg object to the body of the page
  svg = d3
    .select(spectraChart.value!)
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto;");

  // add axis
  svg
    .append("g")
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
    .attr("transform", `translate(${margin.left}, 0)`)
    .call(d3.axisLeft(y))
    .call((g) =>
      g
        .append("text")
        .attr("x", -margin.left)
        .attr("y", 20)
        .attr("fill", "currentColor")
        .attr("text-anchor", "start")
        .text("Average intensity (%)"),
    );

  // create line
  const globalLine = d3
    .line<number>()
    .x((_, i) => x((i * binSize.value + low.value) * ((40 - offset) / 4096) + offset))
    .y((d, _) => y(d * (100 / 255)));

  // Add the line to chart
  svg
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
  const line = d3
    .line<number>()
    .x((_, i) => x((i * binSize.value + low.value) * ((40 - offset) / 4096) + offset))
    .y((d, _) => y(d * (100 / 255)));

  // Add the line to chart
  svg
    .append("path")
    .datum(selectionData)
    .attr("fill", "none")
    .attr("stroke", "green")
    .attr("stroke-width", 1)
    .attr("id", "selectionLine")
    .attr("d", line)
    .style("opacity", 0);

  // modify visibility based on checkbox status
  updateSelectionSpectrum();

  // remove previous element lines
  svg.select("#elementLine").remove();
  svg.selectAll("line").remove();

  // create line
  const elementLine = d3
    .line<number>()
    .x((_, i) => x((i * binSize.value + low.value) * ((40 - offset) / 4096) + offset))
    .y((d, _) => y(d * (100 / 255)));

  // Add the line to chart
  svg
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
    svg
      .append("line")
      .style("stroke", "grey")
      .style("stroke-width", 1)
      .attr("x1", x((index * binSize.value + low.value) * ((40 - offset) / 4096) + offset))
      .attr("y1", 30)
      .attr("x2", x((index * binSize.value + low.value) * ((40 - offset) / 4096) + offset))
      .attr("y2", 430);
  });

  // modify visibility based on checkbox status
  updateElement();
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
    try {
      loadingGlobal.value = true;
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
      const data = await response.json();
      globalData = data;
      makeChart();
      loadingGlobal.value = false;
    } catch (e) {
      console.error("Error getting global average spectrum", e);
    }
  }
}

/**
 * Plots the average graph of the given pixels.
 * For now assumes that the pixels are given in the raw data coordinate system.
 * @param selection Json object representing the selection.
 */
async function getSelectionSpectrum(selection: SelectionAreaSelection) {
  if (ready && selection.type != undefined && selectionChecked.value) {
    // Request body for selection
    const request_body = flipSelectionAreaSelection(selection, (await getTargetSize()).height);

    try {
      // Abort any previous requests
      abortController.abort();
      abortController = new AbortController();
      loadingSelection.value = true;

      //make api call
      const response = await fetch(`${config.api.endpoint}/${datasource.value}/get_selection_spectrum`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request_body),
        signal: abortController.signal,
      });
      const data = await response.json();
      selectionData = data;
      makeChart();
      loadingSelection.value = false;
    } catch (e) {
      console.error("Error getting selection average spectrum", e);
    }
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
    svg.selectAll("line").remove();
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
    svg.selectAll("line").style("opacity", 0);
  } else {
    svg.selectAll("line").style("opacity", 1);
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
      <div class="mt-1 flex items-center">
        <Select v-model:model-value="selectedElement" @update:model-value="updateElementSpectrum">
          <SelectTrigger class="ml-1 w-32">
            <SelectValue placeholder="Select an element" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Elements</SelectLabel>
              <SelectItem :value="element.name" v-for="element in trimmedList" :key="element.name">
                {{ element.name }}
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
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
      </div>
    </div>
  </Window>
</template>
