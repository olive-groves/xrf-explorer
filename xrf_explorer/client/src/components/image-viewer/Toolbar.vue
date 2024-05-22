<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Slider } from "@/components/ui/slider";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";
import { Hand, Search, LassoSelect, Settings } from "lucide-vue-next";
import { ToolState } from "./types";

const state = defineModel<ToolState>("state");
</script>

<template>
  <div
    class="absolute bottom-0 left-1/2 z-50 my-2 flex w-min -translate-x-1/2 space-x-1 rounded-md border bg-background
      p-1 shadow-sm"
  >
    <ToggleGroup type="single" v-model:model-value="state!.tool">
      <ToggleGroupItem value="grab" class="size-8 p-2" title="Grab">
        <Hand />
      </ToggleGroupItem>
      <ToggleGroupItem value="lens" class="size-8 p-2" title="Lens">
        <Search />
      </ToggleGroupItem>
      <ToggleGroupItem value="lasso" class="size-8 p-2" title="Lasso selection">
        <LassoSelect />
      </ToggleGroupItem>
    </ToggleGroup>
    <Separator orientation="vertical" class="h-8" />
    <Popover>
      <PopoverTrigger as-child>
        <Button variant="ghost" class="size-8 p-2 hover:text-muted-foreground" title="Tool configuration">
          <Settings />
        </Button>
      </PopoverTrigger>
      <PopoverContent class="m-2 w-60 space-y-4 p-2 pb-4">
        <div class="grid gap-3">
          <div class="flex items-center justify-between">
            <Label for="movementspeed">Movement speed</Label>
            <div class="text-muted-foreground">
              {{ state!.movementSpeed[0] }}
            </div>
          </div>
          <Slider id="movementspeed" :min="0.1" :max="3.0" :step="0.1" v-model:model-value="state!.movementSpeed" />
        </div>
        <div class="grid gap-3">
          <div class="flex items-center justify-between">
            <Label for="scrollspeed">Scroll speed</Label>
            <div class="text-muted-foreground">
              {{ state!.scrollSpeed[0] }}
            </div>
          </div>
          <Slider id="scrollspeed" :min="0.1" :max="3.0" :step="0.1" v-model:model-value="state!.scrollSpeed" />
        </div>
        <div v-if="state!.tool == 'lens'">
          <div class="grid gap-3">
            <div class="flex items-center justify-between">
              <Label for="lenszoom">Lens size </Label>
              <div class="text-muted-foreground">
                {{ state!.lensSize[0] }}
              </div>
            </div>
            <Slider id="lenszoom" :min="1" :max="400" :step="10" v-model:model-value="state!.lensSize" />
          </div>
        </div>
      </PopoverContent>
    </Popover>
  </div>
</template>
