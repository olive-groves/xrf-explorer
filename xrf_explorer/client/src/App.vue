<script setup lang="ts">
import { Header } from "@/components";
import { TestWindow } from "@/windows";
import { DraggableContainer } from "@/components/functional/draggable";
</script>

<template>
  <div class="w-[100vw] h-[100vh]">
    <img
      src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg/2048px-Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg"
      class="w-full h-full -z-20 fixed left-0 top-0" />
    <Header />
    <DraggableContainer class="w-full h-full fixed left-0 top-0">
      <TestWindow />
    </DraggableContainer>
  </div>
</template>
