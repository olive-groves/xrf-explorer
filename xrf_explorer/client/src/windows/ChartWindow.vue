<script setup lang="ts">
import { inject, ref } from "vue";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { FrontendConfig } from "@/lib/config";
import * as d3 from "d3";
import { datasource } from "@/lib/appState";
import { exportableElements } from "@/lib/export";

const chart = ref<HTMLElement>();
const config = inject<FrontendConfig>("config")!;

type Element = {
  name: string;
  average: number;
};

// Chart type checkboxes
const barChecked = ref(false);
const lineChecked = ref(false);

// SVG container
let svg = d3.select(chart.value!);
let x = d3.scaleBand();
let y = d3.scaleLinear();

// Elemental data averages
let dataAverages: Element[];

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
 * Set up the chart's SVG container and axes.
 */
function setup() {
  // Declare chart dimensions and margins
  const margin = { top: 30, right: 30, bottom: 70, left: 60 },
    width = 860 - margin.left - margin.right,
    height = 400 - margin.top - margin.bottom;
  const max = d3.max(dataAverages, (d) => d.average) as number;

  // Select SVG container
  svg = d3
    .select(chart.value!)
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto;");

  // Declare the horizontal position scale
  x = d3
    .scaleBand()
    .domain(dataAverages.map((d) => d.name))
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

  // Setup chart for export
  exportableElements["Elemental chart"] = chart.value!;
}

/**
 * Add the line chart to the SVG container.
 */
function setupLineChart() {
  // Add a line generator
  const line = d3
    .line<Element>()
    .x((d) => x(d.name)! + x.bandwidth() / 2)
    .y((d) => y(d.average));

  // Adds opposite colored line behind the colored line for better visibility
  svg
    .append("path")
    .datum(dataAverages)
    .attr("fill", "none")
    .attr("stroke", "hsl(var(--background))")
    .attr("stroke-width", 4)
    .attr("d", line);

  // Adds the colored line
  svg
    .append("path")
    .datum(dataAverages)
    .attr("fill", "none")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 2)
    .attr("d", line);
}

/**
 * Add the bar chart to the SVG container.
 */
function setupBarChart() {
  // Add data
  svg
    .selectAll("svg")
    .data(dataAverages)
    .join("rect")
    .attr("x", (d) => x(d.name) as number)
    .attr("y", (d) => y(d.average))
    .attr("width", x.bandwidth())
    .attr("height", (d) => y(0) - y(d.average))
    .attr("fill", "currentColor");
}

/**
 * Show the bar and/or line chart. This function includes the fetching of the elemental data
 * which is displayed in the chart.
 */
async function showChart() {
  try {
    // Whether the elemental data was fetched properly
    const fetched: boolean = await fetchAverages(config.api.endpoint);
    if (fetched) {
      // Checks if the data was fetched properly
      if (barChecked.value) setupBarChart(); // Display the bar chart
      if (!barChecked.value) {
        svg.selectAll("rect").remove(); // Remove existing bar chart
      }
      if (lineChecked.value) setupLineChart(); // Display the line chart
      if (!lineChecked.value) {
        svg.selectAll("path").remove(); // Remove existing line chart
      }
    }
  } catch (e) {
    console.error("Error fetching average data", e);
  }
}

/**
 * Set up the chart when the window is mounted. This function includes the fetching of the elemental data
 * which is displayed in the chart.
 */
async function setupChart() {
  try {
    // Whether the elemental data was fetched properly
    const fetched: boolean = await fetchAverages(config.api.endpoint);
    if (fetched) {
      // Checks if the data was fetched properly
      setup(); // Display the chart
    }
  } catch (e) {
    console.error("Error fetching average data", e);
  }
}
</script>

<template>
  <Window title="Elemental charts" @window-mounted="setupChart" location="right">
    <!-- CHART TYPE CHECKBOXES -->
    <div class="mx-2 space-y-1">
      <p class="font-bold">Select which type of chart to show:</p>
      <div class="mt-1 flex items-center">
        <Checkbox id="barCheck" v-model:checked="barChecked" @update:checked="showChart" />
        <label class="ml-1" for="globalCheck">Bar chart</label>
      </div>
      <div class="mt-1 flex items-center">
        <Checkbox id="lineCheck" v-model:checked="lineChecked" @update:checked="showChart" />
        <label class="ml-1" for="selectionCheck">Line chart</label>
      </div>
    </div>
    <!-- CHART DISPLAY -->
    <Separator class="mb-1 mt-2" />
    <p class="ml-2 font-bold">Average abundance chart:</p>
    <AspectRatio :ratio="5 / 2">
      <svg class="ml-2" ref="chart"></svg>
    </AspectRatio>
  </Window>
</template>
