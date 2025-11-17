<script lang="ts">
import { defineComponent } from "vue";
import StitchMappingBase from "./StitchMappingBase.vue";
import StitchMappingGreyscale from "./StitchMappingGreyscale.vue";

export default defineComponent({
  name: "StitchMappingViewer",
  components: {
    StitchMappingBase,
    StitchMappingGreyscale,
  }
});
</script>

<template>
  <div class="flex w-full h-full">
    <!-- Greyscale viewer -->
    <div class="w-1/2 h-full border-r border-black">
      <StitchMappingGreyscale class="w-full h-full" />
    </div>

    <!-- Base viewer -->
    <div class="w-1/2 h-full">
      <StitchMappingBase class="w-full h-full" />
    </div>
  </div>
</template>