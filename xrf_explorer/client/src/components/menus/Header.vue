<script setup lang="ts">
// Import the necessary components
import {
  Menubar,
  MenubarCheckboxItem,
  MenubarContent,
  MenubarMenu,
  MenubarSeparator,
  MenubarTrigger,
} from "@/components/ui/menubar";
import { ExportMenu, FileMenu, MainMenu, WindowMenu } from ".";
import { windowState } from "@/components/ui/window/state.ts";
import { appState, datasource } from "@/lib/appState.ts";
import {inject} from "vue";
import {FrontendConfig} from "@/lib/config.ts";

const config = inject<FrontendConfig>("config")!;

/**
 *
 */
async function sendStitchingRequest() {
  const json1 = {
    type: "elemental",
    preview: false,
    contextual_image: "RGB_resized.jpg",
    down_scaling: 0.1,
    fragments: [
      {
        datacube_file: "element1.dms",
        rpl_file: "spectral1.rpl",
        rotation: 270,
        local_points: {
          top_left: [40, 88],
          top_right: [566, 25],
          bottom_left: [92, 534],
          bottom_right: [669, 544],
        },
        target_points: {
          top_left: [31, 127],
          top_right: [988, 5],
          bottom_left: [124, 935],
          bottom_right: [1167, 955],
        },
      },
      {
        datacube_file: "element2.dms",
        rpl_file: "spectral2.rpl",
        rotation: 270,
        local_points: {
          top_left: [19, 238],
          top_right: [741, 270],
          bottom_left: [63, 570],
          bottom_right: [695, 560],
        },
        target_points: {
          top_left: [15, 1485],
          top_right: [1331, 1535],
          bottom_left: [104, 2100],
          bottom_right: [1251, 2071],
        },
      },
      {
        datacube_file: "element3.dms",
        rpl_file: "spectral3.rpl",
        rotation: 90,
        local_points: {
          top_left: [207, 48],
          top_right: [666, 29],
          bottom_left: [117, 499],
          bottom_right: [762, 519],
        },
        target_points: {
          top_left: [1841, 61],
          top_right: [2678, 20],
          bottom_left: [1667, 891],
          bottom_right: [2864, 911],
        },
      },
      {
        datacube_file: "element4.dms",
        rpl_file: "spectral4.rpl",
        rotation: 90,
        local_points: {
          top_left: [94, 232],
          top_right: [661, 155],
          bottom_left: [90, 639],
          bottom_right: [793, 761],
        },
        target_points: {
          top_left: [1661, 1428],
          top_right: [2702, 1262],
          bottom_left: [1679, 2161],
          bottom_right: [2946, 2370],
        },
      },
    ],
  };
  const response = await fetch(`${config.api.endpoint}/Stitch/stitch_datacubes/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(json1),
  });
}
</script>

<template>
  <Menubar class="m-0 h-min w-full justify-between rounded-none border-0 border-b">
    <div class="flex">
      <MainMenu />
      <FileMenu />
      <WindowMenu />
      <MenubarMenu>
        <MenubarTrigger @click="sendStitchingRequest"> Stitch </MenubarTrigger>
      </MenubarMenu>
    </div>
    <div>
      <ExportMenu />
    </div>
  </Menubar>
</template>
