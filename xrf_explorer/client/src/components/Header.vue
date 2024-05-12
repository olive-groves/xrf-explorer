<script setup lang="ts">
import {
  Menubar,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarSeparator,
  MenubarSub,
  MenubarSubContent,
  MenubarSubTrigger,
  MenubarTrigger,
} from '@/components/ui/menubar';
import { WindowMenu } from '@/components/ui/window';
import { DialogMenuItem } from '@/components/ui/dialog';

import { useColorMode } from '@vueuse/core';

import { computed } from 'vue'
import { useFetch } from '@vueuse/core';

// FUNCTIONALITY FOR THE FILES MENU
const API_URL = 'http://localhost:8001/api'

// Fetch files
const { data } = useFetch(`${API_URL}/files`).get().json()
const files = computed(() => {
  return data.value as Array<string>;
})

const colorMode = useColorMode({
  initialValue: "dark"
});
</script>

<template>
  <Menubar class="w-full h-min m-0 rounded-none border-0 border-b">
    <MenubarMenu>
      <MenubarTrigger class="font-bold">
        XRF-Explorer
      </MenubarTrigger>
      <MenubarContent>
        <MenubarItem>
          Github
        </MenubarItem>
        <MenubarSeparator />
        <MenubarItem>
          Preferences
        </MenubarItem>
        <MenubarSub>
          <MenubarSubTrigger>
            Theme
          </MenubarSubTrigger>
          <MenubarSubContent>
            <MenubarItem @click="colorMode = 'light'">
              Light mode
            </MenubarItem>
            <MenubarItem @click="colorMode = 'dark'">
              Dark mode
            </MenubarItem>
          </MenubarSubContent>
        </MenubarSub>
        <MenubarSeparator />
        <MenubarItem>
          Documentation
        </MenubarItem>
      </MenubarContent>
    </MenubarMenu>
    <MenubarMenu>
      <MenubarTrigger>
        File
      </MenubarTrigger>
      <MenubarContent>
        <DialogMenuItem id="upload_file">
          Upload files
        </DialogMenuItem>
        <MenubarSeparator />
        <div>
          <DialogMenuItem v-for="file in files" :key="file" :id="`open_file_${file}`">
            {{ file }}
          </DialogMenuItem>
        </div>
      </MenubarContent>
    </MenubarMenu>
    <WindowMenu>
      <MenubarItem>
        Reset views
      </MenubarItem>
    </WindowMenu>
  </Menubar>
</template>