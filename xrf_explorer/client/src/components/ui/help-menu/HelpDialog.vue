<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { helpState } from "@/lib/helpState";
import { faqWindowOpen } from "@/lib/windowState";
import { getTooltipByKey } from "@/lib/useToolTips";
import { snakeCase } from "change-case";

interface Props {
  /**
   * Title of the help menu dialog.
   */
  title?: string;
  /**
   * To check whether it should be shown or not.
   */
  enabled?: boolean;
}

const props = defineProps<Props>();
const open = ref(false);

// Combine global and local enable states
const isEnabled = computed(() => props.enabled !== false && helpState.enabled);

// Close automatically if disabled while open
watch(isEnabled, (enabled) => {
  if (!enabled) open.value = false;
});
</script>

<template>
  <div v-if="isEnabled" class="inline-flex items-center">
    <button
      class="mx-1 flex size-4 items-center justify-center rounded-full border border-gray-400 p-0 text-[10px]
        leading-none text-gray-500 hover:border-gray-600 hover:text-gray-700"
      title="Help"
      @click.stop="open = true"
    >
      ?
    </button>

    <Dialog v-if="isEnabled" v-model:open="open">
      <DialogContent class="max-w-md">
        <DialogTitle>{{ props.title || "Help" }}</DialogTitle>
        <p class="mt-2 text-sm text-foreground">
          {{ getTooltipByKey("help_menu." + snakeCase(props.title || "error")) }}
        </p>
        <Button
          variant="link"
          class="mt-3"
          @click="
            faqWindowOpen = true;
            open = false;
          "
        >
          Open FAQ
        </Button>
      </DialogContent>
    </Dialog>
  </div>
</template>
