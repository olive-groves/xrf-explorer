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
} from '@/components/ui/menubar'
import { WindowMenu } from '@/components/ui/window'
</script>

<template>
  <Menubar class="w-min m-2 z-50 fixed">
    <div>
      <div class="h-full content-center font-bold text-nowrap px-3">
        XRF-Explorer
      </div>
    </div>
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