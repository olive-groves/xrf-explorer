<script setup lang="ts">
import { computed, ComputedRef, onMounted, ref } from "vue";
import { ELEMENT_SYMBOLS, ELEMENT_NAMES, ELEMENT_NO_SPECTRAL_DATA } from "./elementSymbols";
import { ElementalChannel } from "@/lib/workspace";
import { initializeChannels } from "@/components/workspace/utils";
import { appState } from "@/lib/appState";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

onMounted(() => {
  // If the channels are not initialized in the global state, initialize them
  if (
    appState.workspace &&
    (!appState.workspace.elementalChannels || appState.workspace.elementalChannels.length === 0)
  ) {
    void initializeChannels(appState.workspace);
  }
});

// Not finished
const trimmedList: ComputedRef<string[]> = computed(() => {
  const channels = appState.workspace?.elementalChannels;
  if (!channels) return [];

  return channels
    .map((element: ElementalChannel) => element.name.replace(/ [A-Z]$/, "")) // Remove " K", " L", etc.
    .filter((name: string) => name !== "Continuum" && name !== "chisq");
});

const props = defineProps<{
  /**
   * The currently selected element symbol.
   */
  modelValue: string; // The selected element symbol
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
  (e: "select", value: string): void; // Emitted when user actively selects an element
}>();

const open = ref(false);

// Periodic table layout (element indices, null for empty spaces). IUPAC format.
const periodicTableLayout = [
  [1, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, 2],
  [3, 4, null, null, null, null, null, null, null, null, null, null, 5, 6, 7, 8, 9, 10],
  [11, 12, null, null, null, null, null, null, null, null, null, null, 13, 14, 15, 16, 17, 18],
  [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],
  [37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54],
  [55, 56, null, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86],
  [87, 88, null, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118],
  [null, null, null, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71],
  [null, null, null, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103],
];

/**
 * Run when an element is selected (button associated with the element is clicked).
 * @param elementIndex Index of the element that got selected.
 */
function handleSelect(elementIndex: number) {
  const oldSymbol = props.modelValue;
  if (oldSymbol === ELEMENT_SYMBOLS[elementIndex - 1]) {
    // Unselect if the same element is clicked again
    emit("update:modelValue", "No element");
    emit("select", "No element");
    open.value = false;
    return;
  }
  const symbol = ELEMENT_SYMBOLS[elementIndex - 1];
  emit("update:modelValue", symbol);
  emit("select", symbol);
  open.value = false;
}
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <button
        class="inline-flex h-9 w-fit items-center justify-between rounded-md border bg-background px-3 py-2 text-sm
          shadow-sm hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring"
      >
        <span>{{ props.modelValue }}</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="ml-2 size-4 opacity-50"
        >
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </button>
    </PopoverTrigger>
    <PopoverContent class="w-auto p-3" align="start">
      <div class="overflow-x-auto">
        <div class="inline-grid gap-0.5" style="grid-template-columns: repeat(18, minmax(0, 1fr))">
          <template v-for="(row, rowIndex) in periodicTableLayout" :key="rowIndex">
            <!-- Add an empty row between the main part and the extension -->
            <div v-if="rowIndex === 7" class="col-span-full h-2"></div>

            <template v-for="(elementIndex, colIndex) in row" :key="`${rowIndex}-${colIndex}`">
              <div
                v-if="rowIndex === 5 && colIndex === 2"
                class="flex size-8 cursor-default items-center justify-center rounded border border-border bg-red-500/30
                  text-[0.6rem] font-semibold text-foreground"
              >
                57-71
              </div>

              <div
                v-else-if="rowIndex === 6 && colIndex === 2"
                class="flex size-8 cursor-default items-center justify-center rounded border border-border bg-red-500/60
                  text-[0.6rem] font-semibold text-foreground"
              >
                89-103
              </div>

              <button
                v-else-if="elementIndex !== null && ELEMENT_SYMBOLS[elementIndex - 1]"
                :disabled="ELEMENT_NO_SPECTRAL_DATA.includes(elementIndex)"
                @click="handleSelect(elementIndex)"
                :class="[
                  'size-8 rounded border-2 text-xs font-semibold transition-colors',
                  ELEMENT_NO_SPECTRAL_DATA.includes(elementIndex)
                    ? 'cursor-not-allowed border-secondary bg-secondary/50 text-muted-foreground'
                    : props.modelValue === ELEMENT_SYMBOLS[elementIndex - 1]
                      ? 'border-primary bg-primary text-primary-foreground'
                      : [
                          trimmedList.includes(ELEMENT_SYMBOLS[elementIndex - 1]) ? 'border-primary' : 'border-border',
                          rowIndex === 7
                            ? 'bg-red-500/30 hover:bg-red-500/40'
                            : rowIndex === 8
                              ? 'bg-red-500/60 hover:bg-red-500/70'
                              : 'bg-secondary hover:bg-secondary/50',
                        ],
                ]"
                :title="
                  ELEMENT_NO_SPECTRAL_DATA.includes(elementIndex)
                    ? `${ELEMENT_NAMES[elementIndex - 1]} - No Theoretical data`
                    : ELEMENT_NAMES[elementIndex - 1]
                "
              >
                <div class="flex h-full flex-col items-center justify-center gap-0 leading-none">
                  <span class="my-0 text-[0.6rem] leading-none">{{ elementIndex }}</span>
                  <span class="my-0 leading-none">{{ ELEMENT_SYMBOLS[elementIndex - 1] }}</span>
                </div>
              </button>

              <div v-else class="size-8"></div>
            </template>
          </template>
        </div>
        <div class="my-2 flex h-full flex-col items-center justify-center">
          <span class="opacity-70">Elements with a yellow border are present in the project's elemental data</span>
        </div>
      </div>
    </PopoverContent>
  </Popover>
</template>
