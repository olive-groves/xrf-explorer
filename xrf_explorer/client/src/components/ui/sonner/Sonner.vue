<script lang="ts" setup>
import { Toaster as Sonner, type ToasterProps } from "vue-sonner";

const props = defineProps<ToasterProps>();
</script>

<template>
  <Sonner
    class="custom-toaster group"
    v-bind="props"
    :toast-options="{
      classes: {
        toast: `group toast group-[.custom-toaster]:bg-background group-[.custom-toaster]:text-foreground
        group-[.custom-toaster]:border-border group-[.custom-toaster]:shadow-lg`,
        description: 'group-[.toast]:text-muted-foreground',
        actionButton: 'group-[.toast]:bg-primary group-[.toast]:text-primary-foreground',
        cancelButton: 'group-[.toast]:bg-muted group-[.toast]:text-muted-foreground',
      },
    }"
  />
</template>
