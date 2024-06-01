<script setup lang="ts">
import { Card } from "@/components/ui/card";
import { Eye, EyeOff } from "lucide-vue-next";
import { Window } from "@/components/ui/window";
import { computed, watch } from "vue";
import { appState, elements } from "@/lib/appState";
import { Input } from "@/components/ui/input";
import { LabeledSlider } from "@/components/ui/slider";

/**
 * Watches the elemental channels defined in the workspace.
 * Upon every change to these elemental channels, the selection is updated to reflect the workspace.
 */
watch(
  elements,
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

/**
 * Gets the name of a channel from the workspace.
 * @param index - The channel to get the name of.
 * @returns The name of the channel.
 */
function getChannelName(index: number): string {
  return elements.value.find((channel) => channel.channel == index)?.name ?? "";
}

const selection = computed(() => appState.selection.elements);
</script>

<template>
  <Window title="Elemental channels" location="left">
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
          <div class="mt-1.5" v-text="getChannelName(channel.channel)" />
          <div class="flex">
            <Label
              v-if="channel.selected"
              title="Select color"
              :for="`color_${channel.channel}`"
              class="size-8 rounded-md p-2 hover:bg-accent"
            >
              <div
                :for="`color_${channel.channel}`"
                class="size-4 rounded-md border border-border"
                :style="{
                  'background-color': channel.color,
                }"
              />
            </Label>
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
        <LabeledSlider
          v-if="channel.selected"
          label="Intensity thresholds"
          :min="0"
          :max="1"
          :default="[0, 1]"
          v-model="channel.thresholds"
        />
      </Card>
    </div>
  </Window>
</template>
