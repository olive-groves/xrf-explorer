<script setup lang="ts">
// Import the necessary component
import { LayerSystem } from "@/components/image-viewer";
</script>

<template>
  <Window title="Layers" help="Select what layers of the painting to show" location="left">
    <div class="p-2">
      <LayerSystem />
    </div>
  </Window>
</template>
