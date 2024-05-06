<script setup lang="ts">
import Button from "@/components/ui/button/Button.vue";
</script>

<template>
  <div style="background-color: #2b2828" class="grid gap-4 grid-cols-12 p-1">
    <Button size="lg"> Files </Button>
    <Button size="lg"> Channels </Button>
    <div
      style="display: inline"
      class="col-start-5 col-end-9 mx-auto text-3xl font-bold"
    >
      XRF Explorer 2.0
    </div>
    <Button size="lg" class="col-start-11">Viewer</Button>
    <Button size="lg" class="col-start-12">Reset</Button>
  </div>
</template>

<style scoped></style>
