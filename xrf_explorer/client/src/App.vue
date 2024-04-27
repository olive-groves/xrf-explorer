<script setup lang="ts">
import { Header, TestWindow } from "@/components";
import { Window, WindowContainer } from "@/components/ui/window";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
</script>

<template>
  <div class="grid grid-cols-1 grid-rows-[min-content_1fr] w-[100vw] h-[100vh]">
    <Header />
    <WindowContainer class="w-full h-full border-t">
      <Window title="Example Window" id="example">
        <div class="space-y-2">
          <div>
            A cool window
          </div>
          <Separator />
          <div>
            This is a separator, it separates things.
          </div>
          <img class="w-48 mx-auto" src="https://iiif.micr.io/vYtZI/full/600,/0/default.webp" />
          <div>
            You can basically put everything you want in these windows.
          </div>
          <Button>
            Cool button :0
          </Button>
        </div>
      </Window>
      <Window title="Second wider window" id="example_2" opened :width="30">
        Here is some more content for in the window, but what happens if the text gets too long and needs to be
        wrapped
        to seperate lines?
      </Window>
      <TestWindow />
    </WindowContainer>
  </div>
  <!-- <canvas class="h-full w-full" id="glcanvas"/> -->
</template>
