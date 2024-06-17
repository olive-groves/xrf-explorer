<script setup lang="ts">
import { SelectionAreaSelection, SelectionAreaType } from "@/lib/selection";
import { Point2D, deepClone, sortRectanglePoints } from "@/lib/utils";
import { useElementBounding } from "@vueuse/core";
import { computed, ref, toRef, watch } from "vue";

const props = defineProps<{
  /**
   * The active selection type for selections made in this selection area.
   */
  type?: SelectionAreaType;
  /**
   * The size of a clickable margin in pixels.
   */
  clickMargin?: number;
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
}>();

const type = toRef(props, "type");
watch(type, () => {
  // Reset selection upon changing tool
  candidateType.value = undefined;
  candidatePoints.value = [];
});

/**
 * The selection object that is updated by the selection area when a selection is made.
 * Will not contain an invalid selection.
 */
const model = defineModel<SelectionAreaSelection>({ required: true });

const element = ref<SVGElement>();
const box = useElementBounding(element);

/**
 * Variables for the candidate selection.
 */
const candidateType = ref<SelectionAreaType | undefined>(undefined);
const candidatePoints = ref<Point2D[]>([]);

/**
 * True if the last candidate point is close to the first candidate point.
 */
const nearInitial = computed(() => {
  const first = candidatePoints.value[0];
  const last = candidatePoints.value[candidatePoints.value.length - 1];
  const dx = (100 * Math.abs(first.x - last.x)) / props.w;
  const dy = (100 * Math.abs(first.y - last.y)) / props.h;
  return dx * dx + dy * dy <= 16;
});

/**
 * The path for the last line in the candidate lasso selection.
 */
const lastLassoCandidateLine = computed(() => {
  const length = candidatePoints.value.length;
  const first = candidatePoints.value[length - 2];
  const last = nearInitial.value ? candidatePoints.value[0] : candidatePoints.value[length - 1];
  return `M${first.x} ${first.y} L${last.x} ${last.y}`;
});

/**
 * Maps a client location of a mouse event to the location in selection coordinates.
 * @param client - The client location.
 * @returns - The location in the selection coordinates.
 */
function mapLocation(client: Point2D): Point2D {
  return {
    x: props.x + ((client.x - box.left.value) * props.w) / box.width.value,
    y: props.y + props.h - ((client.y - box.top.value) * props.h) / box.height.value,
  };
}

/**
 * Handles a click event for polygon selection.
 * @param event - The mouse event.
 */
function onClick(event: MouseEvent) {
  if (props.type == SelectionAreaType.Lasso) {
    const point = mapLocation({ x: event.clientX, y: event.clientY });
    if (candidateType.value == SelectionAreaType.Lasso) {
      // If selection is already started, end it if the clicked point is close to the starting position.
      // Add a new point to the selection otherwise.
      if (nearInitial.value) {
        if (candidatePoints.value.length > 3) {
          model.value = {
            type: SelectionAreaType.Lasso,
            points: candidatePoints.value.slice(0, -1),
          };
        } else {
          model.value.type = undefined;
        }
        candidateType.value = undefined;
        candidatePoints.value = [];
      } else {
        candidatePoints.value.push(point);
      }
    } else {
      // Start new lasso selection
      candidateType.value = SelectionAreaType.Lasso;
      candidatePoints.value = [deepClone(point), deepClone(point)];
    }
  }
}

/**
 * Starts a rectangle selection.
 * @param event - The mouse event.
 */
function onMouseDown(event: MouseEvent) {
  if (props.type == SelectionAreaType.Rectangle) {
    const point = mapLocation({ x: event.clientX, y: event.clientY });
    candidateType.value = SelectionAreaType.Rectangle;
    candidatePoints.value = [deepClone(point), deepClone(point)];
  }
}

/**
 * Ends a rectangle selection.
 */
function onMouseUp() {
  if (candidateType.value == SelectionAreaType.Rectangle) {
    if (
      candidatePoints.value[0].x != candidatePoints.value[1].x &&
      candidatePoints.value[0].y != candidatePoints.value[1].y
    ) {
      model.value = {
        type: SelectionAreaType.Rectangle,
        points: sortRectanglePoints([candidatePoints.value[0], candidatePoints.value[1]]),
      };
    } else {
      model.value.type = undefined;
    }
    candidateType.value = undefined;
    candidatePoints.value = [];
  }
}

/**
 * Updates the last candidate point to follow the mouse.
 * @param event - The mouse event.
 */
function onMouseMove(event: MouseEvent) {
  if (candidateType.value != undefined) {
    const index = candidatePoints.value.length - 1;
    const point = mapLocation({ x: event.clientX, y: event.clientY });
    candidatePoints.value[index].x = point.x;
    candidatePoints.value[index].y = point.y;
  }
}
</script>

<template>
  <div class="absolute left-0 top-0 size-full">
    <svg
      ref="element"
      class="size-full -scale-y-100 overflow-visible"
      :viewBox="`${props.x} ${props.y} ${props.w} ${props.h}`"
      preserveAspectRatio="none"
      fill="none"
    >
      <!-- DISPLAY FINISHED SELECTION -->
      <rect
        v-if="model.type == SelectionAreaType.Rectangle"
        :x="model.points[0].x"
        :y="model.points[0].y"
        :width="model.points[1].x - model.points[0].x"
        :height="model.points[1].y - model.points[0].y"
        vector-effect="non-scaling-stroke"
        fill-opacity="var(--selection-opacity)"
        class="fill-selection stroke-selection-foreground stroke-2"
      />
      <path
        v-if="model.type == SelectionAreaType.Lasso"
        :d="`M${model.points.map((point) => `${point.x} ${point.y}`).join(' L')} Z`"
        vector-effect="non-scaling-stroke"
        fill-opacity="var(--selection-opacity)"
        class="fill-selection stroke-selection-foreground stroke-2"
      />

      <!-- DISPLAY CANDIDATE SELECTION -->
      <rect
        v-if="candidateType == SelectionAreaType.Rectangle"
        :x="Math.min(candidatePoints[0].x, candidatePoints[1].x)"
        :y="Math.min(candidatePoints[0].y, candidatePoints[1].y)"
        :width="Math.abs(candidatePoints[0].x - candidatePoints[1].x)"
        :height="Math.abs(candidatePoints[0].y - candidatePoints[1].y)"
        vector-effect="non-scaling-stroke"
        class="stroke-primary stroke-2"
      />
      <path
        v-if="candidateType == SelectionAreaType.Lasso"
        :d="`M${candidatePoints
          .slice(0, -1)
          .map((point) => `${point.x} ${point.y}`)
          .join(' L')}`"
        vector-effect="non-scaling-stroke"
        class="stroke-primary stroke-2"
      />
      <path
        v-if="candidateType == SelectionAreaType.Lasso"
        :d="lastLassoCandidateLine"
        vector-effect="non-scaling-stroke"
        class="stroke-primary stroke-2"
      />
    </svg>
    <div
      class="absolute left-0 top-0 size-full"
      :class="{
        'cursor-crosshair': props.type != undefined,
      }"
      :style="{
        margin: `-${props.clickMargin}px`,
        width: `calc(100% + 2 * ${props.clickMargin}px)`,
        height: `calc(100% + 2 * ${props.clickMargin}px)`,
      }"
      @click="onClick"
      @mousedown="onMouseDown"
      @mouseup="onMouseUp"
      @mousemove="onMouseMove"
      @mouseleave="onMouseUp"
    />
  </div>
</template>
