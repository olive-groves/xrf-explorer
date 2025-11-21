import * as d3 from "d3";

/**
 * Clear the whole chart (including axes).
 * @param svg - The SVG element to clear.
 */
export function clearChart(svg: d3.Selection<HTMLElement, unknown, null, undefined>) {
  svg.selectAll("*").remove();
}

export function makeSpectraChart(
  target: HTMLElement,
  data: {
    global: number[];
    selection: number[];
    element: number[];
    elementPeaks: number[];
  },
  params: {
    low: number;
    high: number;
    binSize: number;
    offset: number;
  },
  flags: {
    globalChecked: boolean;
    selectionChecked: boolean;
    elementChecked: boolean;
    selectedElement: string;
  },
  dimensions: {
    width: number;
    height: number;
    margin: { top: number; right: number; bottom: number; left: number };
  },
  zoomState: {
    currentZoomTransform: d3.ZoomTransform | null;
    setZoomTransform: (t: d3.ZoomTransform) => void;
  },
) {
  const svg = d3.select(target);
  clearChart(svg);

  const { width, height, margin } = dimensions;
  const { low, high, binSize, offset } = params;
  const { global: globalData, selection: selectionData, element: elementData, elementPeaks } = data;
  const { globalChecked, selectionChecked, elementChecked, selectedElement } = flags;

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

  const getMax = () => {
    let globalMax: number = d3.max(globalData, (d) => d) as number;
    let selectionMax: number = d3.max(selectionData, (d) => d) as number;

    // Initialize max values if they are NaN
    if (isNaN(globalMax)) globalMax = 0;
    if (isNaN(selectionMax)) selectionMax = 0;

    let max: number;

    // Update the global and selection max values
    if (selectionChecked && !globalChecked) {
      max = selectionMax;
    } else if (globalChecked && !selectionChecked) {
      max = globalMax;
    } else {
      max = Math.max(...[globalMax, selectionMax]);
    }

    return max;
  };

  const max = getMax();

  // Add X and Y axis
  const x = d3
    .scaleLinear()
    .range([margin.left, width - margin.right])
    .domain([low * ((40 - offset) / high) + offset, high * ((40 - offset) / high) + offset]);
  const y = d3
    .scaleLinear()
    .range([height - margin.bottom, margin.top])
    .domain([0, max * (100 / 255)]);

  // append the svg object to the body of the page
  svg
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

  /**
   * Generates a D3 line based on the current binning parameters.
   * @returns - The D3 line.
   */
  function createLine() {
    return d3
      .line<number>()
      .x((_, i) => x((i * binSize + low) * ((40 - offset) / high) + offset))
      .y((d, _) => y(d * (100 / 255)));
  }

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
    .style("opacity", globalChecked ? 1 : 0);

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
    .style("opacity", selectionChecked ? 1 : 0);

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
    .style("opacity", elementChecked && selectedElement != "No element" ? 1 : 0);

  //Add peaks
  elementPeaks.forEach((index) => {
    plotArea
      .append("line")
      .attr("class", "peak-line")
      .style("stroke", "grey")
      .style("stroke-width", 1)
      .attr("x1", x((index * binSize + low) * ((40 - offset) / high) + offset))
      .attr("y1", 30)
      .attr("x2", x((index * binSize + low) * ((40 - offset) / high) + offset))
      .attr("y2", 430)
      .style("opacity", elementChecked && selectedElement != "No element" ? 1 : 0);
  });

  const zoom = d3
    .zoom()
    .scaleExtent([1, 1024])
    .extent([
      [margin.left, margin.top],
      [width - margin.right, height - margin.bottom],
    ])
    .translateExtent([
      [margin.left, margin.top],
      [width - margin.right, height - margin.bottom],
    ])
    .on("zoom", (event) => {
      zoomState.setZoomTransform(event.transform); // Store the current transform
      const newX = event.transform.rescaleX(x);
      const newY = event.transform.rescaleY(y);

      // Update axes
      svg.select(".x-axis").call(d3.axisBottom(newX) as never);
      svg.select(".y-axis").call(d3.axisLeft(newY) as never);

      // Create new line generator with transformed scales
      const zoomedLine = d3
        .line<number>()
        .x((_, i) => newX((i * binSize + low) * ((40 - offset) / high) + offset))
        .y((d) => newY(d * (100 / 255)));

      // Update all lines with zoomed scales
      svg.select("#globalLine").attr("d", zoomedLine(globalData));
      svg.select("#selectionLine").attr("d", zoomedLine(selectionData));
      svg.select("#elementLine").attr("d", zoomedLine(elementData));

      // Update peaks
      svg
        .selectAll(".peak-line")
        .attr("x1", (_, i) =>
          newX((elementPeaks[i] * binSize + low) * ((40 - offset) / high) + offset),
        )
        .attr("x2", (_, i) =>
          newX((elementPeaks[i] * binSize + low) * ((40 - offset) / high) + offset),
        );
    });

  svg.call(zoom as never);

  // Restore the previous zoom transform if it exists
  if (zoomState.currentZoomTransform) {
    svg.call(zoom.transform as never, zoomState.currentZoomTransform);
  } else {
    svg.call(zoom.transform as never, d3.zoomIdentity);
  }

  return svg;
}
