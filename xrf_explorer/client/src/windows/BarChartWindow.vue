<script setup lang="ts">
import { inject, ref } from "vue";
import { Window } from "@/components/ui/window";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { FrontendConfig } from "@/lib/config";
import * as d3 from "d3";

const barchart = ref(null);

const config = inject<FrontendConfig>("config")!;

type Element = {
  name: string;
  average: number;
};

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
  const response: Response = await fetch(`${url}/element_averages`, {
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
        console.log("Successfully fetched averages");
        return true;
      })
      .catch((e) => {
        console.log(e);
        return false;
      });
  } else {
    // Error response
    fetchSuccessful = await response
      .text()
      .then((data) => {
        console.log(data);
        return false;
      })
      .catch((e) => {
        console.log(e);
        return false;
      });
  }

  return fetchSuccessful;
}

/**
 * Set up the bar chart's SVG container, add axes and data.
 */
function setup() {
  // Declare chart dimensions and margins
  const margin = { top: 30, right: 30, bottom: 70, left: 60 },
    width = 860 - margin.left - margin.right,
    height = 400 - margin.top - margin.bottom;
  const max: number = d3.max(dataAverages, (d) => d.average) as number;

  // Select SVG container
  const svg = d3
    .select(barchart.value)
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto;");

  // Declare the horizontal position scale
  const x = d3
    .scaleBand()
    .domain(dataAverages.map((d) => d.name))
    .range([margin.left, width - margin.right])
    .padding(0.1);

  // Declare the vertical position scale
  const y = d3
    .scaleLinear()
    .domain([0, max])
    .range([height - margin.bottom, margin.top]);

  // Add axes
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
    .call((g) =>
      g
        .append("text")
        .attr("x", -margin.left)
        .attr("y", 20)
        .attr("fill", "currentColor")
        .attr("text-anchor", "start")
        .text("↑ Average abundance"),
    )
    .selectAll("text")
    .style("font-size", "18px");

  // Add data
  svg
    .selectAll("svg")
    .data(dataAverages)
    .join("rect")
    .attr("x", (d) => x(d.name) as number)
    .attr("y", (d) => y(d.average))
    .attr("width", x.bandwidth())
    .attr("height", (d) => y(0) - y(d.average))
    .attr("fill", "steelblue");
}

/**
 * Show the bar chart. This function includes the fetching of the elemental data
 * which is displayed in the chart.
 */
async function showChart() {
  try {
    // Whether the elemental data was fetched properly
    const fetched: boolean = await fetchAverages(config.api.endpoint);
    if (fetched) setup(); // If everything went right, display the chart
  } catch (e) {
    console.error("Error fetching average data", e);
  }
}
</script>

<template>
  <Window title="Bar Chart Window" @window-mounted="showChart" opened location="right">
    <AspectRatio :ratio="4 / 3">
      <svg ref="barchart"></svg>
    </AspectRatio>
  </Window>
</template>
