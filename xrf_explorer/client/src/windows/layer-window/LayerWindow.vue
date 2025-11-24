<script setup lang="ts">
// Import the necessary component
import { LayerSystem } from "@/components/image-viewer";
</script>

<template>
  <Window title="Layers" help="Determine what layers to show and modify their properties to make them easier to analyze. Select the lens to dynamically analyze the painting" location="left">
    <div class="p-2">
      <LayerSystem />
    </div>
  </Window>
</template>
