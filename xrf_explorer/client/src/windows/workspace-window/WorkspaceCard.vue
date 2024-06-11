<script setup lang="ts">
import { Settings } from "lucide-vue-next";

const props = defineProps<{
  /**
   * Name of the workspace card.
   */
  name: string;
  /**
   * Description of the workspace card.
   */
  description: string;
}>();

const emit = defineEmits(["settings"]);
</script>

<template>
  <Card class="p-2">
    <div class="flex content-center justify-between">
      <div class="flex content-center space-x-2">
        <div class="aspect-square h-full p-1">
          <slot name="icon" />
        </div>
        <div class="whitespace-nowrap">
          <div v-text="props.name" />
          <div v-text="props.description" class="text-muted-foreground" />
        </div>
      </div>
      <Button variant="ghost" class="size-8 p-2" title="Configure" @click="emit('settings')">
        <Settings />
      </Button>
      <slot />
    </div>
  </Card>
</template>
