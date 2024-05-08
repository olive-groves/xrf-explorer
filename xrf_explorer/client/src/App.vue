<script setup lang="ts">
import { Header } from "@/components";
import { WindowContainer } from "@/components/ui/window";
import { TestWindow } from "@/windows";
import { UploadFileDialog } from "@/components/dialogs";
</script>

<template>
  <div class="w-[100vw] h-[100vh] grid grid-cols-1 grid-rows-[min-content_1fr]">
    <Header />
    <WindowContainer>
      <img
        src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg/2048px-Farmhouse_in_Provence%2C_1888%2C_Vincent_van_Gogh%2C_NGA.jpg"
        class="size-full" />
      <TestWindow />
    </WindowContainer>
    <UploadFileDialog />
  </div>
</template>
