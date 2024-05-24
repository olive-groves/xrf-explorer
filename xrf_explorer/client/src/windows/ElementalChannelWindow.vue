<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Eye, EyeOff } from "lucide-vue-next";
import { Window } from "@/components/ui/window";
import { computed, watch } from "vue";
import { appState } from "@/lib/appState";
import { Input } from "@/components/ui/input";
import { hexToRgb } from "@/lib/utils";

const channels = computed(() => appState.workspace?.elementalChannels);

watch(
  channels,
  (value) => {
    value?.forEach((channel) => {
      if (channel.enabled == true) {
        appState.selection.elements.push({
          channel: channel.channel,
          selected: false,
          color: [255, 255, 255],
          intensity: [1],
        });
      }
    });
  },
  { immediate: true },
);
</script>

<template>
  <Window title="Elemental Channels Window" opened>
    <div v-for="channel in appState.selection.elements" :key="channel.channel" class="p-2">
      <Card class="space-y-2 p-2">
        <div class="flex justify-between">
          <div>
            <div>
              {{ channel.channel }}
            </div>
            <div class="whitespace-nowrap text-muted-foreground">Elemental map of {{ channel.channel }}.</div>
          </div>
          <Input
            default-value="#FFFFFF"
            @update:model-value="(value) => (channel.color = hexToRgb(value as string))"
            type="color"
          />
          <Button
            @click="channel.selected = !channel.selected"
            variant="ghost"
            class="size-8 p-2"
            title="Toggle visibility"
          >
            <Eye v-if="channel.selected" />
            <EyeOff v-else />
          </Button>
        </div>
        <div v-if="channel.selected" class="space-y-2">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div>Channel intensity</div>
              <div>{{ channel.intensity[0] }}</div>
            </div>
            <Slider v-model="channel.intensity" :min="0" :step="0.01" :max="1" class="pb-2" />
          </div>
        </div>
      </Card>
    </div>
  </Window>
</template>
