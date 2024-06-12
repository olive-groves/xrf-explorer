<script setup lang="ts">
import { SelectionAreaSelection, SelectionAreaType } from "@/lib/selection";
import { Point2D, deepClone } from "@/lib/utils";
import { useElementBounding } from "@vueuse/core";
import { computed, ref } from "vue";

const props = defineProps<{
  type?: SelectionAreaType;
  x: number;
  y: number;
  w: number;
  h: number;
}>();

const model = defineModel<SelectionAreaSelection>({ required: true });

const element = ref<SVGElement>();
const box = useElementBounding(element);

const candidateType = ref<SelectionAreaType | undefined>(undefined);
const candidatePoints = ref<Point2D[]>([]);
const nearInitial = computed(() => {
  const first = candidatePoints.value[0];
  const last = candidatePoints.value[candidatePoints.value.length - 1];
  const dx = (100 * Math.abs(first.x - last.x)) / props.w;
  const dy = (100 * Math.abs(first.y - last.y)) / props.h;
  return dx * dx + dy * dy <= 25;
});

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
      if (nearInitial.value) {
        model.value = {
          type: SelectionAreaType.Lasso,
          points: candidatePoints.value.slice(0, -1),
        };
        candidateType.value = undefined;
        candidatePoints.value = [];
      } else {
        candidatePoints.value.push(point);
      }
    } else {
      candidateType.value = SelectionAreaType.Lasso;
      candidatePoints.value = [deepClone(point), deepClone(point)];
    }
  }
}

/**
 *
 * @param event
 */
function onMouseDown(event: MouseEvent) {
  if (props.type == SelectionAreaType.Rectangle) {
    const point = mapLocation({ x: event.clientX, y: event.clientY });
    candidateType.value = SelectionAreaType.Rectangle;
    candidatePoints.value = [deepClone(point), deepClone(point)];
  }
}

/**
 *
 * @param event
 */
function onMouseUp() {
  if (candidateType.value == SelectionAreaType.Rectangle) {
    model.value = {
      type: SelectionAreaType.Rectangle,
      points: [
        {
          x: Math.min(candidatePoints.value[0].x, candidatePoints.value[1].x),
          y: Math.min(candidatePoints.value[0].y, candidatePoints.value[1].y),
        },
        {
          x: Math.max(candidatePoints.value[0].x, candidatePoints.value[1].x),
          y: Math.max(candidatePoints.value[0].y, candidatePoints.value[1].y),
        },
      ],
    };
    candidateType.value = undefined;
    candidatePoints.value = [];
  }
}

/**
 *
 * @param event
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
  <svg
    ref="element"
    class="absolute left-0 top-0 size-full -scale-y-100"
    :viewBox="`${props.x} ${props.y} ${props.w} ${props.h}`"
    preserveAspectRatio="none"
    fill="none"
    @click="onClick"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
    @mousemove="onMouseMove"
    @mouseleave="onMouseUp"
  >
    <!-- FINISHED SELECTION -->
    <rect
      v-if="model.type == SelectionAreaType.Rectangle"
      :x="model.points[0].x"
      :y="model.points[0].y"
      :width="model.points[1].x - model.points[0].x"
      :height="model.points[1].y - model.points[0].y"
      stroke="red"
      stroke-width="2"
      vector-effect="non-scaling-stroke"
      fill="red"
      fill-opacity="0.5"
    />
    <path
      v-if="model.type == SelectionAreaType.Lasso"
      :d="`M${model.points.map((point) => `${point.x} ${point.y}`).join(' L')} Z`"
      stroke="red"
      stroke-width="2"
      vector-effect="non-scaling-stroke"
      fill="red"
      fill-opacity="0.5"
    />

    <!-- CANDIDATE SELECTION -->
    <rect
      v-if="candidateType == SelectionAreaType.Rectangle"
      :x="Math.min(candidatePoints[0].x, candidatePoints[1].x)"
      :y="Math.min(candidatePoints[0].y, candidatePoints[1].y)"
      :width="Math.abs(candidatePoints[0].x - candidatePoints[1].x)"
      :height="Math.abs(candidatePoints[0].y - candidatePoints[1].y)"
      stroke="green"
      stroke-width="2"
      vector-effect="non-scaling-stroke"
    />
    <path
      v-if="candidateType == SelectionAreaType.Lasso"
      :d="`M${candidatePoints
        .slice(0, -1)
        .map((point) => `${point.x} ${point.y}`)
        .join(' L')}`"
      stroke="green"
      stroke-width="2"
      vector-effect="non-scaling-stroke"
    />
    <path
      v-if="candidateType == SelectionAreaType.Lasso"
      :d="lastLassoCandidateLine"
      stroke="green"
      stroke-width="2"
      vector-effect="non-scaling-stroke"
    />
  </svg>
</template>
