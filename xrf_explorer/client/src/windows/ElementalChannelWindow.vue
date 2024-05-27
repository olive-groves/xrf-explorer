<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Eye, EyeOff } from "lucide-vue-next";
import { Window } from "@/components/ui/window";
import { computed, watch } from "vue";
import { appState } from "@/lib/appState";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const channels = computed(() => appState.workspace?.elementalChannels);

watch(
  channels,
  (value) => {
    appState.selection.elements = [];
    value?.forEach((channel) => {
      if (channel.enabled == true) {
        appState.selection.elements.push({
          channel: channel.channel,
          selected: false,
          color: "#FFFFFF",
          thresholds: [0.0, 1.0],
        });
      }
    });
  },
  { immediate: true },
);

const selection = computed(() => appState.selection.elements);
</script>

<template>
  <Window title="Elemental channels" opened>
    <div class="space-y-2 p-2">
      <Card
        v-for="channel in selection"
        :key="channel.channel"
        class="space-y-2 p-2"
        :style="{
          'border-color': channel.selected ? channel.color : 'hsl(var(--border))',
        }"
      >
        <div class="flex justify-between">
          <div>
            <div>
              {{ channel.channel }}
            </div>
            <div class="whitespace-nowrap text-muted-foreground" />
          </div>
          <div class="flex">
            <Label
              v-if="channel.selected"
              :for="`color_${channel.channel}`"
              class="mt-2 size-4 rounded-md border border-border"
              :style="{
                'background-color': channel.color,
              }"
            />
            <Input
              class="hidden"
              :id="`color_${channel.channel}`"
              default-value="#FFFFFF"
              @update:model-value="(value) => (channel.color = value as string)"
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
        </div>
        <div v-if="channel.selected" class="space-y-2">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div>Thresholds</div>
              <div>{{ channel.thresholds[0] }} – {{ channel.thresholds[1] }}</div>
            </div>
            <Slider v-model="channel.thresholds" :min="0" :step="0.01" :max="1" class="pb-2" />
          </div>
        </div>
      </Card>
    </div>
  </Window>
</template>
