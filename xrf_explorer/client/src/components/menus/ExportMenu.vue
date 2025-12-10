<script setup lang="ts">
// Import the necessary functions and components
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarItem } from "@/components/ui/menubar";
import { appState, datasource } from "@/lib/appState";
import { exportElement, exportScene, exportableElements } from "@/lib/export";
import { getTooltipByKey } from "@/lib/useToolTips";
// Makes usage of the change-case library
import { sentenceCase, snakeCase } from "change-case";
</script>

<template>
  <MenubarMenu v-if="appState.user.role !== ''">
    <MenubarTrigger v-if="datasource" :title="getTooltipByKey('toolbar.export')"> Export </MenubarTrigger>
    <MenubarTrigger
      v-else
      class="w-full cursor-not-allowed opacity-50"
      :title="getTooltipByKey('toolbar.export_missing')"
      disabled
    >
      Export
    </MenubarTrigger>
    <MenubarContent v-if="datasource">
      <MenubarItem
        v-if="datasource"
        @click="() => exportScene()"
        :title="datasource ? getTooltipByKey('toolbar.export_painting') : getTooltipByKey('toolbar.export_missing')"
      >
        Painting
      </MenubarItem>
      <div
        v-for="name in Object.keys(exportableElements)"
        :key="name"
        :title="
          exportableElements[name] != null
            ? getTooltipByKey('toolbar.export_' + snakeCase(name))
            : getTooltipByKey('toolbar.export_missing')
        "
      >
        <MenubarItem
          :key="name"
          :disabled="exportableElements[name] == null"
          @click="
            () => {
              if (exportableElements[name] != null) {
                exportElement(snakeCase(name), exportableElements[name]!);
              }
            }
          "
        >
          {{ sentenceCase(name) }}
        </MenubarItem>
      </div>
    </MenubarContent>
  </MenubarMenu>
</template>
