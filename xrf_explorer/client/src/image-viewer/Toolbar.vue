<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Slider } from "@/components/ui/slider";
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Separator } from "@/components/ui/separator";
import { Hand, Search, LassoSelect, Settings } from 'lucide-vue-next';
import { ref } from "vue";
import { ToolState } from "./types";

const selectedTool = ref("grab");

const state = defineModel<ToolState>("state");
</script>

<template>
  <div
    class="w-min my-2 z-50 fixed bottom-0 flex bg-background border p-1 shadow-sm rounded-md space-x-1 left-1/2 -translate-x-1/2">
    <ToggleGroup type="single" v-model:model-value="selectedTool">
      <ToggleGroupItem value="grab" class="p-2 w-8 h-8" title="Grab">
        <Hand />
      </ToggleGroupItem>
      <ToggleGroupItem value="lens" class="p-2 w-8 h-8" title="Lens">
        <Search />
      </ToggleGroupItem>
      <ToggleGroupItem value="lasso" class="p-2 w-8 h-8" title="Lasso selection">
        <LassoSelect />
      </ToggleGroupItem>
    </ToggleGroup>
    <Separator orientation="vertical" class="h-8" />
    <Popover>
      <PopoverTrigger as-child>
        <Button variant="ghost" class="p-2 w-8 h-8 hover:text-muted-foreground" title="Tool configuration">
          <Settings />
        </Button>
      </PopoverTrigger>
      <PopoverContent class="w-60 m-2 space-y-4 p-2 pb-4">
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
      </PopoverContent>
    </Popover>
  </div>
</template>