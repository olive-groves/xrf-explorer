<script setup lang="ts">
import { Window } from "@/components/ui/window";
import { ref, watch } from "vue";
import { DefaultConfig } from "@/lib/config";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import * as d3 from "d3";

const spectraChart = ref(null);
let x: d3.ScaleLinear<number, number, never>;
let y: d3.ScaleLinear<number, number, never>;
let svg: d3.Selection<null, unknown, null, undefined>;

//need to see how to get these variables
const url: string = DefaultConfig.api.endpoint;
const low: number = 50;
const high: number = 2000;
const binSize: number = 32;

interface Point {
  index: number;
  value: number;
}

/**
 * Setup the svg and axis of the graph.
 */
function setup() {
  // set the dimensions and margins of the graph
  const margin = { top: 30, right: 30, bottom: 70, left: 60 },
    width = 860 - margin.left - margin.right,
    height = 600 - margin.top - margin.bottom;
  // Add X and Y axis
  x = d3
    .scaleLinear()
    .range([margin.left, width - margin.right])
    .domain([low, high]);
  y = d3
    .scaleLinear()
    .range([height - margin.bottom, margin.top])
    .domain([0, 255]);

  // append the svg object to the body of the page
  svg = d3
    .select(spectraChart.value)
    //.append("svg")
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

  getElements();
  plotAverageSpectrum(low, high, binSize);
}
const globalChecked = ref(false);
const elementChecked = ref(false);
const selectionChecked = ref(false);
const selectedElement = ref();
const excitation = ref();

/**
 * Plots the average channel spectrum over the whole painting in the chart.
 * @param low Lower channel boundary.
 * @param high Higher channel boundary.
 * @param binSize Number of channels per bin.
 */
async function plotAverageSpectrum(low: number, high: number, binSize: number) {
  try {
    //make api call
    const response = await fetch(
      `${url}/get_average_data?` +
        new URLSearchParams({
          low: low as unknown as string,
          high: high as unknown as string,
          binSize: binSize as unknown as string,
        }),
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );
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
    console.log("Error Getting Global Average Spectrum", e);
  }
}

/**
 * Plots the average graph of the given pixels
 * For now assumes that the pixels are given in the raw data coordinate system.
 * @param pixels Array of selected pixels.
 * @param low Lower channel boundary.
 * @param high Higher channel boundary.
 * @param binSize Number of channels per bin.
 */
async function plotSelectionSpectrum(pixels: Array<[number, number]>, low: number, high: number, binSize: number) {
  try {
    //make api call
    const response = await fetch(
      `${url}/get_selection_spectrum` +
        new URLSearchParams({
          pixels: pixels as unknown as string,
          low: low as unknown as string,
          high: high as unknown as string,
          binSize: binSize as unknown as string,
        }),
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );
    const data = await response.json();

    //remove spectrum of previous selection
    d3.select("#selectionLine").remove();

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
    updateSelection();
  } catch (e) {
    console.log("Error Getting Selection Average Spectrum", e);
  }
}

/**
 * Plots the theoretical spectrum and peaks of an element.
 * @param element Symbol of element to be plotted.
 * @param excitation Excitation energy.
 * @param low Lower channel boundary.
 * @param high Higher channel boundary.
 * @param binSize Number of channels per bin.
 */
async function plotElementSpectrum(element: string, excitation: number, low: number, high: number, binSize: number) {
  if (element != "No element" && element != "" && excitation != null && (excitation as unknown as string) != "") {
    try {
      //make api call
      const response = await fetch(
        `${url}/get_element_spectrum?` +
          new URLSearchParams({
            element: element as string,
            excitation: excitation as unknown as string,
            low: low as unknown as string,
            high: high as unknown as string,
            binSize: binSize as unknown as string,
          }),
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );
      const data = await response.json();
      const spectrum = data[0];

      //remove previous element lines
      d3.select("#elementLine").remove();
      d3.selectAll("line").remove();

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
          .attr("x1", peak.index)
          .attr("y1", 30)
          .attr("x2", peak.index)
          .attr("y2", 430);
      });
    } catch (e) {
      console.log("Error Getting Element theoretical Spectrum", e);
    }
  } else {
    //remove previous element line
    d3.select("#elementLine").remove();
    d3.selectAll("line").remove();
  }

  //modify visibility based on checkbox status
  updateElement();
}

/**
 * Gets the list of all the elements and plots the one selected in the dropdown.
 */
async function getElements() {
  try {
    //make api call
    const response = await fetch(`${url}/element_names`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    const elements = await response.json();
    elements.unshift("No element");
    elements.splice(elements.indexOf("Continuum"), 1);
    elements.splice(elements.indexOf("chisq"), 1);

    //add dropdown menu
    const elementDropdown = document.getElementById("element-dropdown") as HTMLSelectElement;
    elements.forEach(
      (
        element: string, // create dropdown items
      ) => {
        elementDropdown.add(new Option(element));
      },
    );
  } catch (e) {
    console.log("Error Getting Elements", e);
  }
}

/**
 * Updates visibility of global average spectrum.
 */
function updateGlobal() {
  if (globalChecked.value) {
    d3.select("#globalLine").style("opacity", 1);
  } else {
    d3.select("#globalLine").style("opacity", 0);
  }
}

/**
 * Updates visibility of element theoretical spectrum.
 */
function updateElement() {
  if (elementChecked.value) {
    d3.select("#elementLine").style("opacity", 1);
  } else {
    d3.select("#elementLine").style("opacity", 0);
  }
}

/**
 * Updates visibility of selection average spectrum.
 *
 */
function updateSelection() {
  if (selectionChecked.value) {
    d3.select("#selectionLine").style("opacity", 1);
  } else {
    d3.select("#selectionLine").style("opacity", 0);
  }
}

//
/**
 * Plots element spectrum when an elemented is selected in the dropdown.
 */
function updateElementSpectrum() {
  plotElementSpectrum(selectedElement.value, excitation.value, low, high, binSize);
}

//need to connect to selection tool
if (false) {
  const pixels = [];
  plotSelectionSpectrum(pixels, low, high, binSize);
}

//display svg when window is opened
watch(spectraChart, (_n, _o) => {
  if (spectraChart.value != null) {
    setup();
  }
});
</script>

<template>
  <div>
    <Window title="Spectrum" opened>
      <!-- SPECTRA SELECTION -->
      <p class="ml-1 font-bold">Select which spectra to show:</p>
      <div class="mt-1 flex items-center">
        <Checkbox id="globalCheck" v-model="globalChecked" @change="updateGlobal()" />
        <label class="ml-1" for="globalCheck">Global average</label>
      </div>
      <div class="mt-1 flex items-center">
        <Checkbox id="selectionCheck" v-model="selectionChecked" @change="updateSelection()" />
        <label class="ml-1" for="selectionCheck">Selection average</label>
      </div>
      <div class="mt-1 flex items-center">
        <Checkbox id="elementCheck" v-model="elementChecked" @change="updateElement()" />
        <label class="ml-1" for="elementCheck">Element theoretical</label>
      </div>
      <!-- ELEMENT SELECTION -->
      <Separator class="my-2 ml-1" />
      <p class="ml-1 font-bold">Choose element for theoretical spectrum:</p>
      <div class="mt-1 flex items-center">
        <Select id="element-dropdown" v-model="selectedElement">
          <SelectTrigger class="ml-1 w-32">
            <SelectValue placeholder="Select an element" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Elements</SelectLabel>
              <SelectItem value="0"> Element 0 </SelectItem>
              <SelectItem value="1"> Element 1 </SelectItem>
              <SelectItem value="9"> Element 9 </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Button class="ml-4 block w-28" @click="updateElementSpectrum">Show spectra</Button>
      </div>
      <!-- ENERGY SELECTION -->
      <Separator class="my-2 ml-1" />
      <p class="ml-1 font-bold">Choose the excitation energy (keV):</p>
      <Input
        id="excitation-input"
        type="number"
        class="ml-1 mt-1 w-64"
        v-model="excitation"
        @change="updateElementSpectrum()"
      />
      <!-- PLOTTING THE CHART -->
      <Separator class="my-2 ml-1" />
      <p class="ml-1 font-bold">Generated spectra chart:</p>
      <svg class="ml-1" ref="spectraChart"></svg>
    </Window>
  </div>
</template>
