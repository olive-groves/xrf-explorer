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
 * @param target - The HTML element where the chart will be rendered.
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
  // Get the HTML element which contains/will contain the chart and clear it.
  const svg = d3.select(target);
  clearChart(svg);

  // Setup chart foundation
  setupClipPath(svg, dimensions);
  setupSVGAttributes(svg, dimensions);

  // Calculate chart parameters
  const { yAxisMax, globalMax } = calculateYAxisMax(data.global, data.selection, flags);
  const elementScalingFactor = calculateElementScalingFactor(data.element, globalMax, flags.elementChecked);
  const { x, y } = createScales(dimensions, params, yAxisMax);

  // Render chart components
  renderAxes(svg, x, y, dimensions);

  const plotArea = svg.append("g").attr("clip-path", "url(#chart-area-clip)");
  renderSpectralLines(plotArea, data, x, y, params, flags, elementScalingFactor);
  renderPeakLines(plotArea, data.elementPeaks, x, params, dimensions, flags);

  // Setup interactions
  createZoomBehavior(svg, x, y, dimensions, params, data, elementScalingFactor, zoomState);

  return svg;
}

/**
 * Creates a rectangular clipping region that masks chart content to stay within the plot area.
 * Any chart elements (lines, points, etc.) rendered outside this region will be hidden.
 * This prevents data from overlapping the axes and labels.
 * @param svg - The SVG element to which the clip path will be added.
 * @param dimensions - Object containing chart dimensions and margins.
 * @param dimensions.width - Total width of the chart in pixels.
 * @param dimensions.height - Total height of the chart in pixels.
 * @param dimensions.margin - Object containing margins for chart edges.
 * @param dimensions.margin.top - Top margin in pixels.
 * @param dimensions.margin.right - Right margin in pixels.
 * @param dimensions.margin.bottom - Bottom margin in pixels.
 * @param dimensions.margin.left - Left margin in pixels.
 */
function setupClipPath(
  svg: d3.Selection<HTMLElement, unknown, null, undefined>,
  dimensions: { width: number; height: number; margin: { top: number; right: number; bottom: number; left: number } },
) {
  const { width, height, margin } = dimensions;
  svg
    .append("defs")
    .append("clipPath")
    .attr("id", "chart-area-clip")
    .append("rect")
    .attr("x", margin.left)
    .attr("y", margin.top)
    .attr("width", width - margin.left - margin.right)
    .attr("height", height - margin.top - margin.bottom);
}

/**
 * Calculates the maximum Y-axis value based on visible data and checkbox states.
 * @param globalData - Array of intensity values for the global spectrum.
 * @param selectionData - Array of intensity values for the selection spectrum.
 * @param flags - Object controlling which datasets are visible.
 * @param flags.globalChecked - Whether the global spectrum is visible.
 * @param flags.selectionChecked - Whether the selection spectrum is visible.
 * @returns Object containing the calculated Y-axis maximum and the global data maximum.
 */
function calculateYAxisMax(
  globalData: number[],
  selectionData: number[],
  flags: { globalChecked: boolean; selectionChecked: boolean },
): { yAxisMax: number; globalMax: number } {
  let globalMax: number = d3.max(globalData, (d) => d) as number;
  let selectionMax: number = d3.max(selectionData, (d) => d) as number;

  // Initialize max values if they are NaN
  if (isNaN(globalMax)) globalMax = 0;
  if (isNaN(selectionMax)) selectionMax = 0;

  let yAxisMax: number;

  // Update the global and selection max values
  if (flags.selectionChecked && !flags.globalChecked) {
    yAxisMax = selectionMax;
  } else if (flags.globalChecked && !flags.selectionChecked) {
    yAxisMax = globalMax;
  } else {
    yAxisMax = Math.max(...[globalMax, selectionMax]);
  }

  return { yAxisMax, globalMax };
}

/**
 * Calculates the scaling factor for theoretical element data to match the global data peak.
 * Normalizes the element spectrum so its maximum value aligns with the global maximum.
 * This is done to keep the graphs around the same height. Without this, theoretical element data often peaks at 30%+,
 * making it very hard to compare theoretical data with the real data.
 * @param elementData - Array of intensity values for the element spectrum.
 * @param globalMax - The maximum intensity value of the global spectrum.
 * @param elementChecked - Whether the element spectrum is currently visible.
 * @returns The scaling factor to apply to element data values, or 1 if no scaling is needed.
 */
function calculateElementScalingFactor(elementData: number[], globalMax: number, elementChecked: boolean): number {
  if (!elementChecked || elementData.length === 0) {
    return 1;
  }

  const elementMax = d3.max(elementData, (d) => d) as number;
  if (elementMax > 0 && globalMax > 0) {
    return globalMax / elementMax;
  }

  return 1;
}

/**
 * Creates linear scales for the X and Y axes of the chart.
 * The X-axis scale maps energy bins to pixel coordinates with calibration offset applied.
 * The Y-axis scale maps intensity values to pixel coordinates.
 * @param dimensions - Object containing chart dimensions and margins.
 * @param dimensions.width - Total width of the chart in pixels.
 * @param dimensions.height - Total height of the chart in pixels.
 * @param dimensions.margin - Object containing margins for chart edges.
 * @param dimensions.margin.top - Top margin in pixels.
 * @param dimensions.margin.right - Right margin in pixels.
 * @param dimensions.margin.bottom - Bottom margin in pixels.
 * @param dimensions.margin.left - Left margin in pixels.
 * @param params - Object containing spectral binning and energy parameters.
 * @param params.low - Lower bound of the energy range in channels.
 * @param params.high - Upper bound of the energy range in channels.
 * @param params.offset - Energy offset in keV applied to the x-axis for calibration.
 * @param yAxisMax - The maximum value for the Y-axis domain.
 * @returns D3 Scale function for mapping energy channels to respective pixel X and Y coordinates.
 */
function createScales(
  dimensions: { width: number; height: number; margin: { top: number; right: number; bottom: number; left: number } },
  params: { low: number; high: number; offset: number },
  yAxisMax: number,
) {
  const { width, height, margin } = dimensions;
  const { low, high, offset } = params;

  const x = d3
    .scaleLinear()
    .range([margin.left, width - margin.right])
    .domain([low * ((MAX_KEV - offset) / high) + offset, high * ((MAX_KEV - offset) / high) + offset]);

  const y = d3
    .scaleLinear()
    .range([height - margin.bottom, margin.top])
    .domain([0, yAxisMax]);

  return { x, y };
}

/**
 * Sets up basic SVG attributes including dimensions and viewBox.
 * @param svg - The SVG element to configure.
 * @param dimensions - Object containing chart dimensions.
 * @param dimensions.width - Total width of the chart in pixels.
 * @param dimensions.height - Total height of the chart in pixels.
 */
function setupSVGAttributes(
  svg: d3.Selection<HTMLElement, unknown, null, undefined>,
  dimensions: { width: number; height: number },
) {
  const { width, height } = dimensions;
  svg
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto;");
}

/**
 * Renders the X and Y axes with their labels on the chart.
 * The X-axis displays energy in keV, and the Y-axis displays count percentage.
 * @param svg - The SVG element where axes will be rendered.
 * @param x - The D3 scale function for the X-axis.
 * @param y - The D3 scale function for the Y-axis.
 * @param dimensions - Object containing chart dimensions and margins.
 * @param dimensions.width - Total width of the chart in pixels.
 * @param dimensions.height - Total height of the chart in pixels.
 * @param dimensions.margin - Object containing margins for chart edges.
 * @param dimensions.margin.top - Top margin in pixels.
 * @param dimensions.margin.right - Right margin in pixels.
 * @param dimensions.margin.bottom - Bottom margin in pixels.
 * @param dimensions.margin.left - Left margin in pixels.
 */
function renderAxes(
  svg: d3.Selection<HTMLElement, unknown, null, undefined>,
  x: d3.ScaleLinear<number, number>,
  y: d3.ScaleLinear<number, number>,
  dimensions: { width: number; height: number; margin: { top: number; right: number; bottom: number; left: number } },
) {
  const { width, height, margin } = dimensions;

  // Add X axis
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

  // Add Y axis
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
}

/**
 * Creates a D3 line generator for rendering spectral data paths.
 * Converts spectral bin indices and intensity values to SVG path coordinates.
 * @param x - The D3 scale function for the X-axis.
 * @param y - The D3 scale function for the Y-axis.
 * @param params - Object containing spectral binning and energy parameters.
 * @param params.low - Lower bound of the energy range in channels.
 * @param params.high - Upper bound of the energy range in channels.
 * @param params.binSize - Size of each bin in channels.
 * @param params.offset - Energy offset in keV applied to the x-axis for calibration.
 * @param lineOffset - Optional line-specific energy offset override in keV. Defaults to the offset parameter if 0.
 * @param yScaling - Optional scaling factor to apply to all Y-axis values. Defaults to 1 (no scaling).
 * @returns A D3 line generator function that converts array data to SVG path data.
 */
function createLineGenerator(
  x: d3.ScaleLinear<number, number>,
  y: d3.ScaleLinear<number, number>,
  params: { low: number; high: number; binSize: number; offset: number },
  lineOffset: number = 0,
  yScaling: number = 1,
) {
  const { low, high, binSize, offset } = params;
  const actualOffset = lineOffset === 0 ? offset : lineOffset;

  return d3
    .line<number>()
    .x((_, i) => x((i * binSize + low) * ((MAX_KEV - actualOffset) / high) + actualOffset))
    .y((d) => y(d * yScaling));
}

/**
 * Renders all spectral lines (global, selection, and element) on the chart.
 * Each line's visibility is controlled by corresponding flags (representing checkbox status)
 * The element line is scaled by the provided elementScalingFactor to align with the global peak.
 * @param plotArea - The D3 group element (g) where lines will be rendered.
 * @param data - Object containing spectral data arrays.
 * @param data.global - Array of intensity values for the global spectrum.
 * @param data.selection - Array of intensity values for the selection spectrum.
 * @param data.element - Array of intensity values for the element spectrum.
 * @param x - The D3 scale function for the X-axis.
 * @param y - The D3 scale function for the Y-axis.
 * @param params - Object containing spectral binning and energy parameters.
 * @param params.low - Lower bound of the energy range in channels.
 * @param params.high - Upper bound of the energy range in channels.
 * @param params.binSize - Size of each bin in channels.
 * @param params.offset - Energy offset in keV applied to the x-axis for calibration.
 * @param flags - Object controlling visibility of spectrum lines.
 * @param flags.globalChecked - Whether to display the global spectrum (blue line).
 * @param flags.selectionChecked - Whether to display the selection spectrum (green line).
 * @param flags.elementChecked - Whether to display the element spectrum (orange line).
 * @param flags.selectedElement - Symbol of the currently selected element, or "No element".
 * @param elementScalingFactor - Scaling factor to apply to element spectrum values for peak alignment.
 */
function renderSpectralLines(
  plotArea: d3.Selection<SVGGElement, unknown, null, undefined>,
  data: { global: number[]; selection: number[]; element: number[] },
  x: d3.ScaleLinear<number, number>,
  y: d3.ScaleLinear<number, number>,
  params: { low: number; high: number; binSize: number; offset: number },
  flags: { globalChecked: boolean; selectionChecked: boolean; elementChecked: boolean; selectedElement: string },
  elementScalingFactor: number,
) {
  // Global line
  const globalLine = createLineGenerator(x, y, params);
  plotArea
    .append("path")
    .datum(data.global)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 1)
    .attr("id", "globalLine")
    .attr("d", globalLine)
    .style("opacity", flags.globalChecked ? 1 : 0);

  // Selection line
  const selectionLine = createLineGenerator(x, y, params);
  plotArea
    .append("path")
    .datum(data.selection)
    .attr("fill", "none")
    .attr("stroke", "green")
    .attr("stroke-width", 1)
    .attr("id", "selectionLine")
    .attr("d", selectionLine)
    .style("opacity", flags.selectionChecked ? 1 : 0);

  // Theoretical element line with scaling
  const elementLine = createLineGenerator(x, y, params, 0, elementScalingFactor);
  plotArea
    .append("path")
    .datum(data.element)
    .attr("fill", "none")
    .attr("stroke", "orange")
    .attr("stroke-width", 1)
    .attr("id", "elementLine")
    .attr("d", elementLine)
    .style("opacity", flags.elementChecked && flags.selectedElement != "No element" ? 1 : 0);
}

/**
 * Renders vertical lines marking theoretical element peaks on the chart.
 * These lines help users identify where specific element characteristic X-rays occur.
 * @param plotArea - The D3 group element (g) where peak lines will be rendered.
 * @param elementPeaks - Array of bin/channel indices where theoretical element peaks occur.
 * @param x - The D3 scale function for the X-axis.
 * @param params - Object containing spectral binning and energy parameters.
 * @param params.low - Lower bound of the energy range in channels.
 * @param params.high - Upper bound of the energy range in channels.
 * @param params.binSize - Size of each bin in channels.
 * @param dimensions - Object containing chart dimensions and margins.
 * @param dimensions.height - Total height of the chart in pixels.
 * @param dimensions.margin - Object containing margins for chart edges.
 * @param dimensions.margin.top - Top margin in pixels.
 * @param dimensions.margin.bottom - Bottom margin in pixels.
 * @param flags - Object controlling visibility of peak lines.
 * @param flags.elementPeaksChecked - Whether to display the peak indicator lines.
 * @param flags.selectedElement - Symbol of the currently selected element, or "No element".
 */
function renderPeakLines(
  plotArea: d3.Selection<SVGGElement, unknown, null, undefined>,
  elementPeaks: number[],
  x: d3.ScaleLinear<number, number>,
  params: { low: number; high: number; binSize: number },
  dimensions: { height: number; margin: { top: number; bottom: number } },
  flags: { elementPeaksChecked: boolean; selectedElement: string },
) {
  const { low, high, binSize } = params;
  const { height, margin } = dimensions;

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
      .style("opacity", flags.elementPeaksChecked && flags.selectedElement != "No element" ? 1 : 0);
  });
}

/**
 * Creates and configures the zoom and pan behavior for the chart.
 * Allows users to zoom in/out and pan across the chart area while maintaining axis constraints.
 * @param svg - The SVG element to which zoom behavior will be attached.
 * @param x - The D3 scale function for the X-axis.
 * @param y - The D3 scale function for the Y-axis.
 * @param dimensions - Object containing chart dimensions and margins.
 * @param dimensions.width - Total width of the chart in pixels.
 * @param dimensions.height - Total height of the chart in pixels.
 * @param dimensions.margin - Object containing margins for chart edges.
 * @param dimensions.margin.top - Top margin in pixels.
 * @param dimensions.margin.right - Right margin in pixels.
 * @param dimensions.margin.bottom - Bottom margin in pixels.
 * @param dimensions.margin.left - Left margin in pixels.
 * @param params - Object containing spectral binning and energy parameters.
 * @param params.low - Lower bound of the energy range in channels.
 * @param params.high - Upper bound of the energy range in channels.
 * @param params.binSize - Size of each bin in channels.
 * @param params.offset - Energy offset in keV applied to the x-axis for calibration.
 * @param data - Object containing spectral data arrays and element peaks.
 * @param data.global - Array of intensity values for the global spectrum.
 * @param data.selection - Array of intensity values for the selection spectrum.
 * @param data.element - Array of intensity values for the element spectrum.
 * @param data.elementPeaks - Array of bin/channel indices where element peaks occur.
 * @param elementScalingFactor - Scaling factor applied to element spectrum values.
 * @param zoomState - Object managing the zoom/pan state of the chart.
 * @param zoomState.currentZoomTransform - The current D3 zoom transform, or null if not zoomed.
 * @param zoomState.setZoomTransform - Callback function to persist the current zoom transform.
 * @returns The D3 zoom behavior object.
 */
function createZoomBehavior(
  svg: d3.Selection<HTMLElement, unknown, null, undefined>,
  x: d3.ScaleLinear<number, number>,
  y: d3.ScaleLinear<number, number>,
  dimensions: { width: number; height: number; margin: { top: number; right: number; bottom: number; left: number } },
  params: { low: number; high: number; binSize: number; offset: number },
  data: { global: number[]; selection: number[]; element: number[]; elementPeaks: number[] },
  elementScalingFactor: number,
  zoomState: {
    currentZoomTransform: d3.ZoomTransform | null;
    setZoomTransform: (t: d3.ZoomTransform) => void;
  },
) {
  const { width, height, margin } = dimensions;
  const { low, high, binSize, offset } = params;

  const zoom = d3
    .zoom()
    .scaleExtent([1, 1024])
    .extent([
      [margin.left, margin.top],
      [width - margin.right, height - margin.bottom],
    ])
    .on("zoom", (event) => {
      // Constrain panning to prevent going into negative X and Y directions
      let transform = event.transform;

      // Calculate the maximum allowed translation based on data coordinates
      const maxTx = margin.left - transform.k * x(0);
      const minTy = height - margin.bottom - transform.k * y(0);

      // Clamp the translation values
      if (transform.x > maxTx || transform.y < minTy) {
        transform = d3.zoomIdentity
          .translate(Math.min(transform.x, maxTx), Math.max(transform.y, minTy))
          .scale(transform.k);

        svg.call(zoom.transform as never, transform);
      }

      zoomState.setZoomTransform(transform);
      const newX = transform.rescaleX(x);
      const newY = transform.rescaleY(y);

      // Update axes
      svg.select(".x-axis").call(d3.axisBottom(newX) as never);
      svg.select(".y-axis").call(d3.axisLeft(newY) as never);

      // Create zoomed line generators
      const zoomedLine = d3
        .line<number>()
        .x((_, i) => newX((i * binSize + low) * ((MAX_KEV - offset) / high) + offset))
        .y((d) => newY(d));

      const zoomedElementLine = d3
        .line<number>()
        .x((_, i) => newX((i * binSize + low) * (MAX_KEV / high)))
        .y((d) => newY(d * elementScalingFactor));

      // Update all lines
      svg.select("#globalLine").attr("d", zoomedLine(data.global));
      svg.select("#selectionLine").attr("d", zoomedLine(data.selection));
      svg.select("#elementLine").attr("d", zoomedElementLine(data.element));

      // Update peaks
      svg
        .selectAll(".peak-line")
        .attr("x1", (_, i) => newX((data.elementPeaks[i] * binSize + low) * (MAX_KEV / high)))
        .attr("x2", (_, i) => newX((data.elementPeaks[i] * binSize + low) * (MAX_KEV / high)));
    });

  svg.call(zoom as never);

  // Restore previous zoom transform
  if (zoomState.currentZoomTransform) {
    svg.call(zoom.transform as never, zoomState.currentZoomTransform);
  } else {
    svg.call(zoom.transform as never, d3.zoomIdentity);
  }

  return zoom;
}
