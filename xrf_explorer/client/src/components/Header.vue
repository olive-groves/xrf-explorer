<script setup lang="ts">
import {
  Menubar,
  // MenubarCheckboxItem,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  //   MenubarRadioGroup,
  //   MenubarRadioItem,
  MenubarSeparator,
  MenubarSub,
  MenubarSubContent,
  MenubarSubTrigger,
  //   MenubarShortcut,
  //   MenubarSub,
  //   MenubarSubContent,
  //   MenubarSubTrigger,
  MenubarTrigger,
} from '@/components/ui/menubar';
import { WindowMenu } from '@/components/ui/window';

import { useColorMode } from '@vueuse/core';

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
        Workspace
      </MenubarTrigger>
      <MenubarContent>
        <MenubarItem>
          Recent #1
        </MenubarItem>
        <MenubarItem>
          Recent #2
        </MenubarItem>
        <MenubarItem>
          Recent #3
        </MenubarItem>
        <MenubarSeparator />
        <MenubarItem>
          Open workspace
        </MenubarItem>
        <MenubarSub>
          <MenubarSubTrigger>
            Open recent
          </MenubarSubTrigger>
          <MenubarSubContent>
            <MenubarItem>
              Recent #1
            </MenubarItem>
            <MenubarItem>
              Recent #2
            </MenubarItem>
            <MenubarItem>
              Recent #3
            </MenubarItem>
            <MenubarItem>
              Recent #4
            </MenubarItem>
            <MenubarItem>
              Recent #5
            </MenubarItem>
            <MenubarItem>
              Recent #6
            </MenubarItem>
          </MenubarSubContent>
        </MenubarSub>
        <MenubarItem>
          New workspace
        </MenubarItem>
      </MenubarContent>
    </MenubarMenu>
    <WindowMenu />
  </Menubar>
</template>