import * as d3 from "d3";

/**
 * Clear the whole chart (including axes).
 * @param svg - The SVG element to clear.
 */
export function clearChart(svg: d3.Selection<HTMLElement, unknown, null, undefined>) {
  svg.selectAll("*").remove();
}
