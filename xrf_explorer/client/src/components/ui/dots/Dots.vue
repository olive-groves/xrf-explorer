<script setup lang="ts">
import { computed, ref } from 'vue'
import { appState } from '@/lib/appState';
import { Sphere } from 'three';
import { number } from 'mathjs';
const glcontainer = ref<HTMLDivElement | null>(null);
const glcanvas = ref<HTMLCanvasElement | null>(null);

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


  zoom: number;


  sp: [number, number][];

}>();

/**
 * Event handler for the onClick event on the glcanvas.
 * @param event - The mouse event.
 */
function onClick(event: MouseEvent) {
  if (event.button == 2) {
    // Prevent opening of context menu.
    event.preventDefault();
  }
  console.log("klinkk")
  

}

type Cross = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  strokeWidth: number;
};

function createCross(cx: number, cy: number) {
  const size = Math.min(100 * Math.exp(props.zoom), 200)
  const strokeWidth = Math.min(5 * Math.exp(props.zoom), 10)
  return [
    // horizontal line
    {
      x1: cx - size / 2,
      y1: cy,
      x2: cx + size / 2,
      y2: cy,
      strokeWidth
    },
    // vertical line
    {
      x1: cx,
      y1: cy - size / 2,
      x2: cx,
      y2: cy + size / 2,
      strokeWidth
    }
  ] satisfies Cross[];
}
const crosses = computed(() => {
  return props.sp.flatMap(([x, y]) => createCross(x, y));
});


</script>

<template>
    <div class="absolute left-0 top-0 size-full"
    @click="onClick"
    >
        <svg
        ref="element"
        class="size-full -scale-y-100 overflow-visible"
        :viewBox="`${x} ${y} ${w} ${h}`"
        preserveAspectRatio="none"
        fill="none"
        @click="onClick"
        >

        <!-- <line x1="90" y1="90" x2="91" y2="90" stroke="red" :stroke-width="zoom + 4.1" />
        <line x1="90.5" y1="88" x2="90.5" y2="92" stroke="red" :stroke-width="1" vector-effect="scaling-stroke" /> -->

        <line
            v-for="(c, i) in crosses"
            :key="i"
            :x1="c.x1"
            :y1="c.y1"
            :x2="c.x2"
            :y2="c.y2"
            stroke="red"
            :stroke-width="c.strokeWidth"
        />



      <!-- DISPLAY FINISHED SELECTION -->

        </svg>
    </div>
</template>