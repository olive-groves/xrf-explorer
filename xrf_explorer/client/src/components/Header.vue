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
import { FileMenu } from '@/components/menus';

// Color mode
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
        File
      </MenubarTrigger>
      <MenubarContent>
        <DialogMenuItem id="upload_file">
          Upload files
        </DialogMenuItem>
        <MenubarSeparator />
        <FileMenu />
      </MenubarContent>
    </MenubarMenu>
    <WindowMenu>
      <MenubarItem>
        Reset views
      </MenubarItem>
    </WindowMenu>
  </Menubar>
</template>