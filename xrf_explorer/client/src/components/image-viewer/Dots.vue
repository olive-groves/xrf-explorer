<script setup lang="ts">
import { computed } from "vue";
import { checkSelectPoint } from "./stitchPoints";
import { selectedGrayscaleIndex, getPointsForGray, hasBase } from "./stitchPoints";

const props = defineProps<{
  /**
   * The x coordinate of the bottom left corner in the viewbox.
   */
  x: number;
  /**
   * The y coordinate of the bottom left corner in the viewbox.
   */
  y: number;
  /**
   * The width of the viewbox.
   */
  w: number;
  /**
   * The height of the viewbox.
   */
  h: number;
  /**
   * The current zoom level.
   */
  zoom: number;
  /**
   * Whether to show grayscale mapping points or base mapping points.
   */
  grayMapping: boolean;
}>();

type Cross = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  strokeWidth: number;
  id: number;
};
/**
 * Function to create a cross shape at given coordinates.
 * @param cx X coordinate.
 * @param cy Y coordinate.
 * @param id Identifier for the cross.
 * @returns Array of line segments representing the cross.
 */
function createCross(cx: number, cy: number, id: number) {
  const size = Math.min(100 * Math.exp(props.zoom), 200);
  const strokeWidth = Math.min(5 * Math.exp(props.zoom), 10);
  return [
    // horizontal line
    {
      x1: cx - size / 2,
      y1: cy,
      x2: cx + size / 2,
      y2: cy,
      strokeWidth,
      id,
    },
    // vertical line
    {
      x1: cx,
      y1: cy - size / 2,
      x2: cx,
      y2: cy + size / 2,
      strokeWidth,
      id,
    },
  ] satisfies Cross[];
}
// const crosses = computed(() => {
//   if (!selectedGrayscaleIndex) {return}
//   getPointsForGray(selectedGrayscaleIndex)

//   return grayscalePoints.getFlatMap(([x, y]) => createCross(x, y));
// });

const crosses = computed(() => {
  const idx = selectedGrayscaleIndex.value;
  if (idx == null) return [];

  const points = getPointsForGray(idx);

  if (props.grayMapping) {
    return points.flatMap((p) => createCross(p.gray.x, p.gray.y, p.id));
  } else {
    // return points.flatMap(p => createCross(p.base.x, p.base.y));
    return points.filter(hasBase).flatMap((p) => createCross(p.base.x, p.base.y, p.id));
  }
});
</script>

<template>
  <div class="absolute left-0 top-0 size-full">
    <svg
      ref="element"
      class="size-full -scale-y-100"
      :viewBox="`${x} ${y} ${w} ${h}`"
      preserveAspectRatio="none"
      fill="none"
    >
      <!-- DISPLAY CROSSES -->
      <line
        v-for="(c, i) in crosses"
        :key="i"
        :x1="c.x1"
        :y1="c.y1"
        :x2="c.x2"
        :y2="c.y2"
        :stroke="checkSelectPoint(c.id) ? 'green' : 'red'"
        :stroke-width="c.strokeWidth"
      />
      <!-- DISPLAY LABELS -->
      <g transform="scale(1, -1)">
        <text
          v-for="c in crosses"
          :key="'label-' + c.id"
          :x="Math.min((c.x1 + c.x2) / 2 + 5 * Math.exp(props.zoom), (c.x1 + c.x2) / 2 + 5)"
          :y="Math.max(-(c.y1 + c.y2) / 2 - 10 * Math.exp(props.zoom), -(c.y1 + c.y2) / 2 - 15)"
          :font-size-adjust="Math.min(1 * Math.exp(props.zoom), 3)"
          fill="black"
          dominant-baseline="middle"
        >
          {{ c.id + 1 }}
        </text>
      </g>
      <!-- DISPLAY FINISHED SELECTION -->
    </svg>
  </div>
</template>
