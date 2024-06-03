<script setup lang="ts">
import { ComputedRef, inject, ref, computed, watch } from "vue";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { FrontendConfig } from "@/lib/config";
import * as d3 from "d3";
import { ElementSelection } from "@/lib/selection";
import { appState, datasource } from "@/lib/appState";

const chart = ref(null);
const config = inject<FrontendConfig>("config")!;

type Element = {
  name: string;
  average: number;
};

// Chart type checkboxes
const barChecked = ref(false);
const lineChecked = ref(false);

// SVG container
let svg = d3.select(chart.value);
let x = d3.scaleBand();
let y = d3.scaleLinear();

// Elemental data averages
let dataAverages: Element[] = [];

// Visibility for all elements
const elementSelection: ComputedRef<ElementSelection[]> = computed(() => appState.selection.elements);

// Visibility of only selected elements
let displayedSelection: ElementSelection[] = [];

// Actual displayed data, i.e. elements which are selected
let selectedData: Element[] = [];

// Whether we should display the averages of elements outside the selection in grey
const displayAll = ref(false);

/**
 * Fetch the average elemental data for each of the elements, and store it
 * in the `dataAverages` array.
 * @param url URL to the server API endpoint which provides the elemental data.
 * @returns True if the averages were fetched successfully, false otherwise.
 */
async function fetchAverages(url: string) {
  // Make API call
  const response: Response = await fetch(`${url}/${datasource.value}/element_averages`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  let fetchSuccessful: boolean = false;

  // Check that fetching the names was successful
  if (response.ok) {
    // Save the names
    fetchSuccessful = await response
      .json()
      .then((data) => {
        dataAverages = data;
        console.debug("Successfully fetched averages");
        return true;
      })
      .catch((e) => {
        console.error(e);
        return false;
      });
  } else {
    // Error response
    fetchSuccessful = await response
      .text()
      .then((data) => {
        console.debug(data);
        return false;
      })
      .catch((e) => {
        console.error(e);
        return false;
      });
  }

  return fetchSuccessful;
}

/**
 * Mask out the element data of the elements which are selected to not be visible.
 * @param selection The selection of elements.
 */
function maskData(selection: ElementSelection[]) {
  displayedSelection = selection.filter((element) => element.selected);

  selectedData = dataAverages.filter((_, index) =>
    displayedSelection.some((elementVis) => elementVis.channel == index),
  );
}

/**
 * Set up the chart's SVG container, add axes.
 * @param data Element data array that we want to display on the chart.
 */
function setupChart(data: Element[]) {
  // Clear all previous instances of the chart
  clearChart();

  // Declare chart dimensions and margins
  const margin = { top: 30, right: 30, bottom: 70, left: 60 },
    width = 860 - margin.left - margin.right,
    height = 400 - margin.top - margin.bottom;
  const max: number = d3.max(data, (d) => d.average) as number;

  // Select SVG container
  svg
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto;");

  // Declare the horizontal position scale
  x = d3
    .scaleBand()
    .domain(data.map((d) => d.name))
    .range([margin.left, width - margin.right])
    .padding(0.1);

  // Declare the vertical position scale
  y = d3
    .scaleLinear()
    .domain([0, max])
    .range([height - margin.bottom, margin.top]);

  // Adjust axes
  svg
    .append("g")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).tickSizeOuter(0))
    .selectAll("text")
    .style("font-size", "18px")
    .attr("transform", "translate(-13, 15)rotate(-45)");

  svg
    .append("g")
    .attr("transform", `translate(${margin.left},0)`)
    .call(d3.axisLeft(y))
    .call((g) => g.select(".domain").remove())
    .call((g) =>
      g
        .selectAll(".tick line")
        .clone()
        .attr("x2", width - margin.left - margin.right)
        .attr("stroke-opacity", 0.1),
    )
    .selectAll("text")
    .style("font-size", "18px");
}

/**
 * Clear the whole chart (including axes).
 */
function clearChart() {
  svg.selectAll("*").remove();
}

/**
 * Clear only the bar chart's bars.
 */
function clearBarChart() {
  svg.selectAll("rect").remove();
}

/**
 * Clear only the line chart's lines.
 */
function clearLineChart() {
  svg.selectAll("path").remove();
}

/**
 * Add the line chart to the SVG container with updated data.
 * @param data Element data array that we want to display on the chart.
 */
function updateLineChart(data: Element[]) {
  // Clear the previous line chart first
  clearLineChart();

  // Add a line generator
  const line = d3
    .line<Element>()
    .x((d) => x(d.name)! + x.bandwidth() / 2)
    .y((d) => y(d.average));

  // Add opposite colored line behind the colored line for better visibility
  svg
    .append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "hsl(var(--background))")
    .attr("stroke-width", 4)
    .attr("d", line);

  // Add the colored line
  svg
    .append("path")
    .datum(dataAverages)
    .attr("fill", "none")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 2)
    .attr("d", line);
}

/**
 * Add the bar chart to the SVG container with updated data.
 * @param data Element data array that we want to display on the chart.
 */
function updateBarChart(data: Element[]) {
  // Clear the previous bar chart first
  clearBarChart();

  // Add data
  svg
    .selectAll("svg")
    .data(data)
    .join("rect")
    .attr("x", (d) => x(d.name) as number)
    .attr("y", (d) => y(d.average))
    .attr("width", x.bandwidth())
    .attr("height", (d) => y(0) - y(d.average))
    .attr("fill", (_, i) => {
      if (displayAll.value) {
        // If it is selected, display it in its own color, otherwise gray
        if (elementSelection.value[i].selected) {
          return elementSelection.value[i].color;
        } else {
          return "hsl(var(--border))";
        }
      } else {
        return displayedSelection[i].color;
      }
    });
}

/**
 * Update the charts being displayed.
 * 
 * @param selection The current selection of elements.
 */
function updateCharts() {
  // Mask the data with the selected elements
  maskData(elementSelection.value);

  // Clear all old stuff
  clearBarChart();
  clearLineChart();

  // If we are displaying all elements, set that to be the data
  if (displayAll.value) {
    selectedData = dataAverages;
  }

  // Set up the chart
  setupChart(selectedData);

  // Add the bar chart
  if (barChecked.value)
    updateBarChart(selectedData);

  // Add the line chart
  if (lineChecked.value)
    updateLineChart(selectedData);
}

/**
 * Set up the window when it is mounted. This function includes the fetching of the elemental data
 * which is displayed in the chart.
 */
async function setupWindow() {
  try {
    // Whether the elemental data was fetched properly
    const fetched: boolean = await fetchAverages(config.api.endpoint);
    if (fetched) {
      // Checks if the data was fetched properly
      updateCharts();
    }
  } catch (e) {
    console.error("Error fetching average data", e);
  }
}

watch(
  elementSelection,
  (selection) => {
    maskData(selection);
    updateCharts();
  },
  { deep: true },
);
</script>

<template>
  <Window title="Elemental charts" @window-mounted="setupWindow" location="right">
    <!-- CHART TYPE CHECKBOXES -->
    <div class="mx-2 space-y-1">
      <p class="font-bold">Select which type of chart to show:</p>
      <div class="mt-1 flex items-center">
        <Checkbox id="barCheck" v-model:checked="barChecked" @update:checked="updateCharts" />
        <label class="ml-1" for="globalCheck">Bar chart</label>
      </div>
      <div class="mt-1 flex items-center">
        <Checkbox id="lineCheck" v-model:checked="lineChecked" @update:checked="updateCharts" />
        <label class="ml-1" for="selectionCheck">Line chart</label>
      </div>
    </div>
    <!-- DISPLAY ALL CHECKBOX -->
    <div class="mt-1 flex items-center">
      <Checkbox id="displayAll" v-model:checked="displayAll" @update:checked="updateCharts" />
      <label class="ml-1" for="displayGrey">Display all elements</label>
    </div>
    <!-- CHART DISPLAY -->
    <Separator class="mb-1 mt-2" />
    <p class="ml-2 font-bold">Average abundance chart:</p>
    <AspectRatio :ratio="5 / 2">
      <svg class="ml-2" ref="chart"></svg>
    </AspectRatio>
  </Window>
</template>
