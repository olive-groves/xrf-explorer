<script setup lang="ts">
import { Menubar } from "@/components/ui/menubar";
import { ExportMenu, FileMenu, TitleMenu, WindowMenu } from ".";
</script>

<template>
  <Menubar class="m-0 h-min w-full justify-between rounded-none border-0 border-b">
    <div class="flex">
      <TitleMenu />
      <FileMenu />
      <WindowMenu />
    </div>
    <div>
      <ExportMenu />
    </div>
  </Menubar>
</template>
