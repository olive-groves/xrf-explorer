<script setup lang="ts">
// Import the necessary components
import { Menubar } from "@/components/ui/menubar";
import { ExportMenu, FileMenu, MainMenu, WindowMenu, UserMenu } from ".";
</script>

<template>
  <Menubar class="m-0 h-min w-full justify-between rounded-none border-0 border-b">
    <div class="flex">
      <MainMenu />
      <FileMenu />
      <WindowMenu />
    </div>
    <div class="flex">
      <UserMenu />
      <ExportMenu />
    </div>
  </Menubar>
</template>
