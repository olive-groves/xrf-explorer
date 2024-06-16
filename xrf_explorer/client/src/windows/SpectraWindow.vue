<script setup lang="ts">
import { computed, ComputedRef, inject, ref, watch } from "vue";
import { FrontendConfig } from "@/lib/config";
import * as d3 from "d3";
import { appState, binned, binSize, datasource, elements, high, low } from "@/lib/appState";
import { SelectionAreaSelection } from "@/lib/selection";
import { exportableElements } from "@/lib/export";
import {
  NumberField,
  NumberFieldContent,
  NumberFieldDecrement,
  NumberFieldIncrement,
  NumberFieldInput,
} from "@/components/ui/number-field";
import { RequestBody } from "./selection";

const spectraChart = ref<HTMLElement>();
let x: d3.ScaleLinear<number, number, never>;
let y: d3.ScaleLinear<number, number, never>;
let svg: d3.Selection<HTMLElement, unknown, null, undefined>;

// Area selection
const areaSelection: ComputedRef<SelectionAreaSelection> = computed(() => appState.selection.imageViewer);
watch(areaSelection, plotSelectionSpectrum, { deep: true, immediate: true });

/**
 * Sets up export of chart.
 */
watch(spectraChart, (value) => (exportableElements["Spectral"] = value), { immediate: true });

const config = inject<FrontendConfig>("config")!;
const url = config.api.endpoint;
let ready: boolean;

/**
 * Represents a point in the chart coordinate system.
 * Index is the x-coordinate, value the y-coordinate.
 * Used to plot each point of the line.
 */
interface Point {
  index: number;
  value: number;
}

const trimmedList: ComputedRef<
  {
    name: string;
    channel: number;
    enabled: boolean;
  }[]
> = computed(() => elements.value.filter((element) => element.name != "Continuum" && element.name != "chisq"));

/**
 * Setup the svg and axis of the graph.
 */
function setup() {
  ready = binned.value;
  watch(binned, () => {
    ready = binned.value;
    plotAverageSpectrum();
  });
  // set the dimensions and margins of the graph
  const margin = { top: 30, right: 30, bottom: 70, left: 60 },
    width = 860 - margin.left - margin.right,
    height = 600 - margin.top - margin.bottom;

  // Add X and Y axis
  x = d3
    .scaleLinear()
    .range([margin.left, width - margin.right])
    .domain([0, (high.value - low.value) / binSize.value]);
  y = d3
    .scaleLinear()
    .range([height - margin.bottom, margin.top])
    .domain([0, 255]);

  // append the svg object to the body of the page
  svg = d3
    .select(spectraChart.value!)
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto;");

  //add axis
  svg
    .append("g")
    .attr("transform", `translate(0, ${height - margin.bottom})`)
    .call(d3.axisBottom(x));

  svg.append("g").attr("transform", `translate(${margin.left}, 0)`).call(d3.axisLeft(y));
  plotAverageSpectrum();
}

const globalChecked = ref(false);
const elementChecked = ref(false);
const selectionChecked = ref(false);
const selectedElement = ref("No element");
const excitation = ref(0);

/**
 * Plots the average channel spectrum over the whole painting in the chart.
 */
async function plotAverageSpectrum() {
  if (ready) {
    try {
      //make api call
      const response = await fetch(`${url}/${datasource.value}/get_average_data`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();

      //create line
      const line = d3
        .line<Point>()
        .x((d: Point) => x(d.index))
        .y((d: Point) => y(d.value));

      // Add the line to chart
      svg
        .append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "steelblue")
        .attr("stroke-width", 1)
        .attr("id", "globalLine")
        .attr("d", line)
        .style("opacity", 0);

      //modify visibility based on checkbox status
      updateGlobal();
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
async function plotSelectionSpectrum(selection: SelectionAreaSelection) {
  if (ready && selection != undefined) {
    // Request body for selection
    const request_body: RequestBody = {
      type: selection.type,
      points: selection.points,
    };
    try {
      //make api call
      const response = await fetch(`${url}/${datasource.value}/get_selection_spectrum`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request_body),
      });
      const data = await response.json();

      //remove spectrum of previous selection
      svg.select("#selectionLine").remove();

      //create line
      const line = d3
        .line<Point>()
        .x((d: Point) => x(d.index))
        .y((d: Point) => y(d.value));

      // Add the line to chart
      svg
        .append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "green")
        .attr("stroke-width", 1)
        .attr("id", "selectionLine")
        .attr("d", line)
        .style("opacity", 0);

      //modify visibility based on checkbox status
      updateSelectionSpectrum();
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
async function plotElementSpectrum(element: string, excitation: number) {
  if (element != "No element" && element != "" && excitation != null && (excitation as unknown as string) != "") {
    try {
      //make api call
      const response = await fetch(`${url}/${datasource.value}/get_element_spectrum/${element}/${excitation}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      const spectrum = data[0];

      //remove previous element lines
      svg.select("#elementLine").remove();
      svg.selectAll("line").remove();

      //create line
      const line = d3
        .line<Point>()
        .x((d: Point) => x(d.index))
        .y((d: Point) => y(d.value));

      // Add the line to chart
      svg
        .append("path")
        .datum(spectrum)
        .attr("fill", "none")
        .attr("stroke", "red")
        .attr("stroke-width", 1)
        .attr("id", "elementLine")
        .attr("d", line)
        .style("opacity", 1);

      //Add peaks
      data[1].forEach((peak: Point) => {
        svg
          .append("line")
          .style("stroke", "grey")
          .style("stroke-width", 1)
          .attr("x1", x(peak.index))
          .attr("y1", 30)
          .attr("x2", x(peak.index))
          .attr("y2", 430);
      });
    } catch (e) {
      console.error("Error getting element theoretical spectrum", e);
    }
  } else {
    //remove previous element line
    svg.select("#elementLine").remove();
    svg.selectAll("line").remove();
  }

  //modify visibility based on checkbox status
  updateElement();
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
  if (elementChecked.value) {
    svg.select("#elementLine").style("opacity", 1);
  } else {
    svg.select("#elementLine").style("opacity", 0);
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
  plotElementSpectrum(selectedElement.value, excitation.value);
}
</script>

<template>
  <Window title="Spectrum" location="right" @window-mounted="setup">
    <div class="mx-2">
      <!-- SPECTRA SELECTION -->
      <div class="space-y-1">
        <p class="font-bold">Select which spectra to show:</p>
        <div class="mt-1 flex items-center">
          <Checkbox id="globalCheck" v-model:checked="globalChecked" @update:checked="updateGlobal" />
          <label class="ml-1" for="globalCheck">Global average</label>
        </div>
        <div class="mt-1 flex items-center">
          <Checkbox id="selectionCheck" v-model:checked="selectionChecked" @update:checked="updateSelectionSpectrum" />
          <label class="ml-1" for="selectionCheck">Selection average</label>
        </div>
        <div class="mt-1 flex items-center">
          <Checkbox id="elementCheck" v-model:checked="elementChecked" @update:checked="updateElement" />
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
      <NumberField id="excitation-input" class="ml-1 mt-1 w-64" v-model="excitation" @change="updateElementSpectrum">
        <NumberFieldContent>
          <NumberFieldInput />
          <NumberFieldDecrement />
          <NumberFieldIncrement />
        </NumberFieldContent>
      </NumberField>
      <!-- PLOTTING THE CHART -->
      <Separator class="mt-2" />
      <p class="ml-1 font-bold">Generated spectra chart:</p>
      <svg class="ml-1" ref="spectraChart"></svg>
    </div>
  </Window>
</template>
