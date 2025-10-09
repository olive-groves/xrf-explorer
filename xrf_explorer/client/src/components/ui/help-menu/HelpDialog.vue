<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { helpState } from "@/lib/helpState"

interface Props {
  title?: string
  text?: string
  enabled?: boolean
}

const props = defineProps<Props>()
const open = ref(false)

// Combine global and local enable states
const isEnabled = computed(() => props.enabled !== false && helpState.enabled)

// Close automatically if disabled while open
watch(isEnabled, (enabled) => {
  if (!enabled) open.value = false
})
</script>

<template>
  <div v-if="isEnabled" class="inline-flex items-center">
    <button
      class="ml-1 mr-1 w-4 h-4 flex items-center justify-center text-[10px] leading-none text-gray-500 border border-gray-400 rounded-full hover:text-gray-700 hover:border-gray-600 p-0"
      title="Help"
      @click.stop="open = true"
    >
      ?
    </button>

    <Dialog v-if="isEnabled" v-model:open="open">
      <DialogContent class="max-w-md">
        <DialogTitle>{{ props.title || 'Help' }}</DialogTitle>
        <p class="text-sm text-gray-600 mt-2">
          {{ props.text || 'No help text provided.' }}
        </p>
      </DialogContent>
    </Dialog>
  </div>
</template>