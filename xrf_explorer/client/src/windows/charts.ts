import * as d3 from "d3";

// The maximum value of the energy axis in keV
// This has been provided to be 40 keV.
const MAX_KEV = 40;

/**
 * Clear the whole chart (including axes).
 * @param svg - The SVG element to clear.
 */
export function clearChart(svg: d3.Selection<HTMLElement, unknown, null, undefined>) {
  svg.selectAll("*").remove();
}

/**
 * Creates an interactive D3.js spectra chart for XRF (X-ray fluorescence) data visualization.
 * This function renders multiple spectral datasets (global, selection, and theoretical element spectra)
 * with zoom and pan capabilities. The chart displays energy (keV) on the x-axis and count percentage on the y-axis.
 * @param target - The HTML element (typically an SVG) where the chart will be rendered.
 * @param data - Object containing the spectral data arrays to be plotted.
 * @param data.global - Array of intensity values representing the global average spectrum across the entire painting.
 * Index represents bin/channel number, value represents average intensity for that bin/channel.
 * @param data.selection - Array of intensity values representing the average spectrum of the selected area.
 * Index represents bin/channel number, value represents average intensity for that bin/channel.
 * @param data.element - Array of intensity values for the theoretical element spectrum.
 * Scaled to match the global spectrum's peak for visual comparison.
 * @param data.elementPeaks - Array of bin/channel indices where theoretical element peaks occur.
 * @param params - Object containing spectral binning and energy range parameters.
 * @param params.low - Lower bound of the energy range in channels (typically 0).
 * @param params.high - Upper bound of the energy range in channels (e.g., 4096).
 * @param params.binSize - Size of each bin in channels, used for x-axis position calculations.
 * @param params.offset - Energy offset in keV applied to the x-axis for calibration purposes.
 * @param flags - Object controlling visibility and display options for chart elements.
 * @param flags.globalChecked - Whether to display the global average spectrum line (blue).
 * @param flags.selectionChecked - Whether to display the selection average spectrum line (green).
 * @param flags.elementChecked - Whether to display the theoretical element spectrum line (orange).
 * @param flags.elementPeaksChecked - Whether to display vertical lines marking theoretical element peaks (grey).
 * @param flags.selectedElement - Symbol of the currently selected element (e.g., "Fe", "Cu", or "No element").
 * @param dimensions - Object defining the chart's size and margins.
 * @param dimensions.width - Total width of the chart in pixels.
 * @param dimensions.height - Total height of the chart in pixels.
 * @param dimensions.margin - Object containing margins for top, right, bottom, and left sides.
 * @param dimensions.margin.top - Top margin in pixels.
 * @param dimensions.margin.right - Right margin in pixels.
 * @param dimensions.margin.bottom - Bottom margin in pixels (includes space for x-axis label).
 * @param dimensions.margin.left - Left margin in pixels (includes space for y-axis label).
 * @param zoomState - Object managing the zoom/pan state of the chart.
 * @param zoomState.currentZoomTransform - The current D3 zoom transform, or null if no zoom is applied.
 * Used to restore zoom state when redrawing the chart.
 * @param zoomState.setZoomTransform - Callback function to update the zoom transform state.
 * Called during zoom/pan events to persist the current transform.
 * @returns The D3 selection of the SVG element containing the rendered chart.
 */
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
    elementPeaksChecked: boolean;
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
  /**
   * Generates a D3 line based on the current binning parameters.
   * @param line_offset Offset in keV to be applied to the line.
   * @param y_scaling Scaling factor to be applied to the Y values of the line.
   * @returns - The D3 line with the given offset and y_scaling.
   */
  function createLine(line_offset: number = offset, y_scaling: number = 1) {
    return d3
      .line<number>()
      .x((_, i) => x((i * binSize + low) * ((MAX_KEV - line_offset) / high) + line_offset))
      .y((d, _) => y(d * y_scaling));
  }

  const svg = d3.select(target);
  clearChart(svg);

  const { width, height, margin } = dimensions;
  const { low, high, binSize, offset } = params;
  const { global: globalData, selection: selectionData, element: elementData, elementPeaks } = data;
  const { globalChecked, selectionChecked, elementChecked, elementPeaksChecked, selectedElement } = flags;

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

    let yAxisMax: number;

    // Update the global and selection max values
    if (selectionChecked && !globalChecked) {
      yAxisMax = selectionMax;
    } else if (globalChecked && !selectionChecked) {
      yAxisMax = globalMax;
    } else {
      yAxisMax = Math.max(...[globalMax, selectionMax]);
    }

    return { yAxisMax, globalMax };
  };

  const { yAxisMax, globalMax } = getMax();

  // Calculate scaling factor for element data
  // Scale element data so its max matches the global max
  let elementScalingFactor = 1;
  if (elementChecked && elementData.length > 0) {
    const elementMax = d3.max(elementData, (d) => d) as number;
    if (elementMax > 0 && globalMax > 0) {
      elementScalingFactor = globalMax / elementMax;
    }
  }

  // Add X and Y axis
  const x = d3
    .scaleLinear()
    .range([margin.left, width - margin.right])
    .domain([low * ((MAX_KEV - offset) / high) + offset, high * ((MAX_KEV - offset) / high) + offset]);
  const y = d3
    .scaleLinear()
    .range([height - margin.bottom, margin.top])
    .domain([0, yAxisMax]);

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

  // create line for element data with scaling applied
  const elementLine = createLine(0, elementScalingFactor);

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
      .attr("x1", x((index * binSize + low) * (MAX_KEV / high)))
      .attr("y1", margin.top)
      .attr("x2", x((index * binSize + low) * (MAX_KEV / high)))
      .attr("y2", height - margin.bottom)
      .style("opacity", elementPeaksChecked && selectedElement != "No element" ? 1 : 0);
  });

  const zoom = d3
    .zoom()
    .scaleExtent([1, 1024])
    .extent([
      [margin.left, margin.top],
      [width - margin.right, height - margin.bottom],
    ])
    .on("zoom", (event) => {
      // Constrain panning to prevent going into negative X and Y directions
      // while allowing unlimited panning in positive directions
      let transform = event.transform;

      // Calculate the maximum allowed translation based on data coordinates
      // We want to prevent data value 0 from appearing in the visible chart area
      // For x: prevent x=0 from panning past the left edge of the chart
      // For y: prevent y=0 from panning past the bottom edge of the chart
      const maxTx = margin.left - transform.k * x(0);
      const minTy = height - margin.bottom - transform.k * y(0);

      // Clamp the translation values to prevent panning into negative directions
      // but allow unlimited panning in positive directions (negative transform values)
      if (transform.x > maxTx || transform.y < minTy) {
        transform = d3.zoomIdentity
          .translate(Math.min(transform.x, maxTx), Math.max(transform.y, minTy))
          .scale(transform.k);

        // Apply the constrained transform back to the SVG
        svg.call(zoom.transform as never, transform);
      }

      zoomState.setZoomTransform(transform); // Store the current transform
      const newX = transform.rescaleX(x);
      const newY = transform.rescaleY(y);

      // Update axes
      svg.select(".x-axis").call(d3.axisBottom(newX) as never);
      svg.select(".y-axis").call(d3.axisLeft(newY) as never);

      // Create new line generator with transformed scales
      const zoomedLine = d3
        .line<number>()
        .x((_, i) => newX((i * binSize + low) * ((MAX_KEV - offset) / high) + offset))
        .y((d) => newY(d));

      // Create scaled line generator for element data
      const zoomedElementLine = d3
        .line<number>()
        .x((_, i) => newX((i * binSize + low) * (MAX_KEV / high)))
        .y((d) => newY(d * elementScalingFactor));

      // Update all lines with zoomed scales
      svg.select("#globalLine").attr("d", zoomedLine(globalData));
      svg.select("#selectionLine").attr("d", zoomedLine(selectionData));
      svg.select("#elementLine").attr("d", zoomedElementLine(elementData));

      // Update peaks
      svg
        .selectAll(".peak-line")
        .attr("x1", (_, i) => newX((elementPeaks[i] * binSize + low) * (MAX_KEV / high)))
        .attr("x2", (_, i) => newX((elementPeaks[i] * binSize + low) * (MAX_KEV / high)));
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
