<script setup lang="ts">
import Button from "@/components/ui/button/Button.vue";

const buttonProps = {
  variant: "outline",
  size: "lg",
  class: "font-bold text-lg",
  style: "background-color: #231f20",
};
</script>

<template>
  <div style="background-color: #2b2828" class="grid gap-4 grid-cols-12 p-1">
    <Button v-bind="buttonProps"> Files </Button>
    <Button v-bind="buttonProps"> View </Button>
    <div
      style="display: inline"
      class="col-start-5 col-end-9 mx-auto text-3xl font-bold"
    >
      XRF Explorer 2.0
    </div>
    <Button v-bind="buttonProps" class="col-start-12">Reset</Button>
  </div>
</template>

<style scoped></style>
