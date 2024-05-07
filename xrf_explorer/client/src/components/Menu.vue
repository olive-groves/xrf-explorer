<script setup lang="ts">
import { ref } from "vue";
import Button from "@/components/ui/button/Button.vue";

const isFilesHovered = ref(false);
</script>

<template>
  <div class="flex p-2 bg-[#2b2828] gap-4">
    <div class="relative">
      <Button
        @mouseover="isFilesHovered = true"
        @mouseleave="isFilesHovered = false"
        size="lg"
        class="file-button-opened"
      >
        Files
      </Button>
      <div
        @mouseover="isFilesHovered = true"
        @mouseleave="isFilesHovered = false"
        v-show="isFilesHovered"
        class="flex flex-col absolute bg-[#2b2828] w-72"
      >
        <div class="p-1 hover:bg-stone-700" @click="$emit('open-upload-modal')">
          Upload new source
        </div>
        <hr class="bg-white h-0.5" />
        <div class="p-1 hover:bg-stone-700">Small pear tree</div>
        <div class="p-1 hover:bg-stone-700">Some other example</div>
        <div class="p-1 hover:bg-stone-700">Damn</div>
      </div>
    </div>
    <Button size="lg"> Channels </Button>
    <div style="display: inline" class="mx-auto text-3xl font-bold">
      XRF Explorer 2.0
    </div>
    <Button size="lg">Viewer</Button>
    <Button size="lg">Reset</Button>
  </div>
</template>

<style scoped>
Button {
  min-width: 160px;
}

.dropdown-element {
  padding: 4px;
}
</style>
