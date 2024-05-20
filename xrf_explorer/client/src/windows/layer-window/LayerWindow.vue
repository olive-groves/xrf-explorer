<script setup lang="ts">
import { Window } from "@/components/ui/window";
import { LayerSystem } from "@/components/image-viewer";
</script>

<template>
  <Window title="Layers" opened>
    <div class="p-1">
      <LayerSystem />
    </div>
  </Window>
</template>
