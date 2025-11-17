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
  <div>
    <StitchMappingBase class="w-full h-full"/>
  </div>
</template>