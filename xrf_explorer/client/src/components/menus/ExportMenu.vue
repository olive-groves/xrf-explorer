<script setup lang="ts">
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarItem } from "@/components/ui/menubar";
import { datasource } from "@/lib/appState";
import { exportElement, exportScene, exportableElements } from "@/lib/export";
import { sentenceCase, snakeCase } from "change-case";
</script>

<template>
  <MenubarMenu>
    <MenubarTrigger> Export </MenubarTrigger>
    <MenubarContent>
      <template v-if="datasource">
        <MenubarItem v-if="datasource" @click="() => exportScene()"> Painting </MenubarItem>
        <MenubarItem
          v-for="name in Object.keys(exportableElements)"
          :key="name"
          @click="() => exportElement(snakeCase(name), exportableElements[name])"
        >
          {{ sentenceCase(name) }}
        </MenubarItem>
      </template>
      <MenubarItem disabled v-else>Nothing to export</MenubarItem>
    </MenubarContent>
  </MenubarMenu>
</template>
