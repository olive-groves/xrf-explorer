<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { Eye, EyeOff } from "lucide-vue-next";
import { Window } from "@/components/ui/window";
import { ref, computed } from "vue";
import { appState } from "@/lib/appState";

const channels = computed(() => appState.workspace?.elementalChannels);
</script>

<template>
  <Window title="Hello" opened>
    <div v-for="channel in channels" :key="channel.name" class="p-2">
      <Card class="space-y-2 p-2">
        <div class="flex justify-between">
          <div>
            <div>
                {{ channel.name }}
            </div>
            <div class="whitespace-nowrap text-muted-foreground">
              description
            </div>
          </div>
          <Button
            variant="ghost"
            class="size-8 p-2"
            title="Toggle visibility"
          >
            <Eye/>
          </Button>
        </div>
        <div class="space-y-2">
          <div class="flex items-center space-x-2">
            <Checkbox/>
            <div class="whitespace-nowrap">Hello 3</div>
          </div>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div>Opacity</div>
              <div>hihi 4</div>
            </div>
            <Slider
              :min="0"
              :step="0.01"
              :max="1"
              class="pb-2"
            />
          </div>
        </div>
      </Card>
    </div>
  </Window>
</template>