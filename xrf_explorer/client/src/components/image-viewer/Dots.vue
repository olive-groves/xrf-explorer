<script setup lang="ts">

</script>

<template>
    <div class="absolute left-0 top-0 size-full">
        <svg
        ref="element"
        class="size-full -scale-y-100 overflow-visible"
        :viewBox="`${3} ${3} ${4} ${5}`"
        preserveAspectRatio="none"
        fill="none"
        >
      <!-- DISPLAY FINISHED SELECTION -->
        <rect
            :x="5"
            :y="4"
            :width="1"
            :height="1"
            vector-effect="non-scaling-stroke"
            fill-opacity="var(--selection-opacity)"
            class="fill-selection stroke-selection-foreground stroke-2"
            />
        </svg>
    </div>
</template>