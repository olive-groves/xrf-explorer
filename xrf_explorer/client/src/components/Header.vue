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
import {
  MenubarWindowItem
} from '@/components/ui/window'
</script>

<template>
  <div class="flex flex-row space-x-2 px-4">
    <div>
      <div class="h-full content-center font-bold select-none">
        XRF-Explorer
      </div>
    </div>
    <Menubar class="rounded-none border-none">
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
      <MenubarMenu>
        <MenubarTrigger>
          View
        </MenubarTrigger>
        <MenubarContent>
          <MenubarWindowItem window_id="example">
            Example #1
          </MenubarWindowItem>
          <MenubarWindowItem window_id="example_2">
            Example #2
          </MenubarWindowItem>
          <MenubarSeparator />
          <MenubarWindowItem window_id="test_window">
            Test window
          </MenubarWindowItem>
        </MenubarContent>
      </MenubarMenu>
      <MenubarMenu>
        <MenubarTrigger>
          Help
        </MenubarTrigger>
        <MenubarContent>
          <MenubarItem>
            Documentation
          </MenubarItem>
          <MenubarItem>
            Github
          </MenubarItem>
          <MenubarSeparator />
          <MenubarItem>
            About
          </MenubarItem>
        </MenubarContent>
      </MenubarMenu>
    </Menubar>
  </div>
</template>