<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { LabeledSlider } from "@/components/ui/slider";
import { stitch } from '@/components/image-viewer/stitchHelper';
import { windowState } from '@/components/ui/window/state';
import { appState } from '@/lib/appState';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { saveWorkspaceDebounced } from '@/components/image-viewer/workspace';

const workspace = computed(() => appState.workspace);

const includeSpectral = ref(true);
const includeElemental = ref(true);

const hasSpectralData = computed(() => {
  const ws = appState.workspace;
  return !!(
    ws && ws.partialSpectralCubes?.length
  );
});

const hasElementalData = computed(() => {
  const ws = appState.workspace;
  return !!(
    ws && ws.partialElementalCubes?.length
  );
});

const showDialog = ref(false);
const showConfirmation = ref(false);

const baseImageOpacity = ref([1.0]);

// Current selected scaling factor
const scalingFactor = ref<number[]>([1.0]);

// size info (optimal)
const estimatedSizeOpt = ref<number | null>(null);

// Percatages data "lost" (optimal)
const lossesOpt = ref<number[] | null>(null);

const scaledLosses = computed(() => {
  if (!lossesOpt.value) return null;

  const factor = scalingFactor.value[0];

  return lossesOpt.value.map(loss =>
    Math.round(loss * factor * 100) / 100
  );
});

const estimatedSize = computed(() => {
  if (estimatedSizeOpt.value === null) return null;

  const factor = scalingFactor.value[0];
  return Math.round(estimatedSizeOpt.value * factor * factor * 10000) / 10000;
});

// Selected contrast value per greyscale
const grayscaleContrast = ref<number[]>([]);


interface GreyscaleState {
    opacity: number[];
    xOffset: number[];
    yOffset: number[];
}

const GreyscaleMapping = ref<GreyscaleState>(   
    {
        opacity: [1.0],
        xOffset: [0],
        yOffset: [0],
    }
);

watch(
  () => workspace.value?.grayscale,
  (grays) => {
    const ws = workspace.value;
    if (!ws || !grays) return;

    grayscaleContrast.value = grays.map((_, idx) => {
      const saved = ws.mapping.grayscaleContrast?.[idx];
      if (saved == null) {
        ws.mapping.grayscaleContrast[idx] = 1.0;
        return 1.0;
      }
      return saved;
    });

    saveWorkspaceDebounced();
  },
  { immediate: true }
);

function updateGreyscaleContrast(idx: number, val: number) {
  grayscaleContrast.value[idx] = val;

  const ws = workspace.value;
  if (ws) {
    ws.mapping.grayscaleContrast[idx] = val;
    saveWorkspaceDebounced();
  }
}

function resetContrast() {
  const ws = workspace.value;
  if (!ws) return;
  grayscaleContrast.value = ws.grayscale.map((_, idx) => {
    ws.mapping.grayscaleContrast[idx] = 1.0;
    return 1.0;
  });
  saveWorkspaceDebounced();
}

function updateSliderBase(val: number[]) {
  baseImageOpacity.value = val;
  // Notify preview viwer about the base opacity change
  try {
    const v = Array.isArray(val) ? val[0] : val;
    window.dispatchEvent(new CustomEvent('stitch:base-opacity-changed', { detail: v }));
  } catch (e) {
    console.warn('Could not dispatch stitch base-opacity event', e);
  }
}

function updateGreyscaleOpacity(val: number[]) {
  GreyscaleMapping.value.opacity = val;

  const opacity = val[0];
  window.dispatchEvent(
    new CustomEvent("stitch:gray-opacity-changed", { detail: opacity })
  );
}

// Function to adjust the X-offset by a pixel delta (+1 or -1)
function nudgeX(delta: number) {
  window.dispatchEvent(
    new CustomEvent("stitch:gray-nudge", { detail: { dx: delta, dy: 0 } })
  );
}

// Function to adjust the Y-offset by a pixel delta (+1 or -1)
function nudgeY(delta: number) {
  window.dispatchEvent(
    new CustomEvent("stitch:gray-nudge", { detail: { dx: 0, dy: delta } })
  );
}

function resetScaling() {
  scalingFactor.value = [1];
}

function resetGreyscaleOffset() {
  window.dispatchEvent(
    new CustomEvent("stitch:reset-offset")
  );
}

function closeDialog() {
  showDialog.value = false;
  showConfirmation.value = false;
}

function confirmStitchingDialog() {
  if (!appState.workspace) return;

  if (includeElemental) {
    stitch(false, "elemental", scalingFactor.value[0], grayscaleContrast.value);
  }
  
  if (includeSpectral) {
    stitch (false, "spectral", scalingFactor.value[0], grayscaleContrast.value);
  }

  appState.workspace.stitchingMode = 'full';
  saveWorkspaceDebounced();

  windowState["stitching"].opened = false;
  windowState["stitching"].disabled = true;
}

async function onModeChanged(e: Event) {
  const { mode, previewInfo } = (e as CustomEvent).detail as {
    mode: "edit" | "preview";
    previewInfo?: {
      losses: number[];
      estimatedSize: number;
      optimalScaling?: number;
    };
  };

  if (mode !== "preview" || !previewInfo) return;

  lossesOpt.value = previewInfo.losses;
  estimatedSizeOpt.value = previewInfo.estimatedSize;

  window.dispatchEvent(
    new CustomEvent("stitch:gray-optimal-scale", {
      detail: { factor: previewInfo.optimalScaling ?? 1 },
    })
  );
}

onMounted(() => {
  window.addEventListener('stitchViewer:stichInfo', onModeChanged as EventListener);
  window.dispatchEvent(
    new CustomEvent("stitchViewer:requestPreviewInfo")
  );
});

onBeforeUnmount(() => {
  window.removeEventListener('stitchViewer:stichInfo', onModeChanged as EventListener);
});

watch(showConfirmation, (open) => {
  if (!open) return;
  includeSpectral.value = true;
  includeElemental.value = true;
});
</script>

<template>
  <Window title="Stitching" location="right">
    <div class="space-y-2 p-2">
      <LabeledSlider
        label="Base Image Opacity"
        :modelValue="baseImageOpacity"
        :min="0.25"
        :max="1"
        :step="0.01"
        @update:modelValue="updateSliderBase"
      />

      <h4 class="font-semibold">{{ `Mapped Data Greyscale` }}</h4>

      <LabeledSlider
        label="Opacity"
        :modelValue="GreyscaleMapping?.opacity ?? [1]"
        :min="0"
        :max="1"
        :step="0.01"
        @update:modelValue="(val: number[]) => updateGreyscaleOpacity(val)"
      />

      <div class="space-y-1">
          <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">X-Offset (pixels)</label>
          <div class="flex items-center space-x-2">
              <Button size="sm" @click="nudgeX(-1)">Left</Button>
              <Button size="sm" @click="nudgeX(1)">Right</Button>
          </div>
      </div>

      <!-- X offset displayed and adjustable via nudge buttons  -->

      <div class="space-y-1">
          <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Y-Offset (pixels)</label>
          <div class="flex items-center space-x-2">
              <Button size="sm" @click="nudgeY(-1)">Up</Button>
              <Button size="sm" @click="nudgeY(1)">Down</Button>
          </div>
      </div>
    
      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="resetGreyscaleOffset">
            Reset offset
          </Button>
        </div>
      </div>

      <div v-if="workspace?.grayscale?.length" class="space-y-3 pt-2 border-t">
        <h4 class="font-semibold">Contrast</h4>
        <div
          v-for="(_, idx) in workspace.grayscale"
          :key="idx"
          class="space-y-1"
        >
          <label class="text-xs text-foreground">
            {{ workspace.grayscale[idx]?.sourceCubeName ?? `Greyscale ${idx + 1}` }}
          </label>

          <LabeledSlider
            :label="''"
            :modelValue="[grayscaleContrast[idx] ?? 1]"
            :min="0.1"
            :max="2"
            :step="0.05"
            @commit="(val: number[]) => updateGreyscaleContrast(idx, val[0])"
          />
        </div>
      </div>

      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="resetContrast">
            Reset contrast
          </Button>
        </div>
      </div>

      <LabeledSlider
        label="Scaling Factor"
        :modelValue="scalingFactor"
        :min="0.25"
        :max="2"
        :step="0.01"
        @update:modelValue="(val: number[]) => (scalingFactor = val)"
      />

      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="resetScaling">
            Reset scaling
          </Button>
        </div>
      </div>

      <div class="space-y-1">
        <div>
          <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          Estimated stitched datacube size:
          </label>
          <span>{{ estimatedSize }} GB</span>
        </div>
      </div>
      <div
        v-if="scaledLosses"
        class="mt-2 space-y-1 text-sm"
      >
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
        Estimated percentage of data used per fragment:
        </label>
        <div
          v-for="(loss, idx) in scaledLosses"
          :key="idx"
          class="flex justify-between font-mono"
        >
          <span>{{ workspace?.grayscale[idx]?.sourceCubeName }}</span>
          <span>{{ loss }} %</span>
        </div>
      </div>
      
      <Button
        variant="destructive"
        class="row-span-3 size-full p-2"
        @click="showConfirmation = true"
      >
      Confirm Stitching
      </Button>

      <div v-if="showConfirmation" class="dialog-overlay">
        <div class="dialog-content">
          <div class="flex flex-col space-y-3">
            <label
             class="text-sm font-medium leading-none"
              >
              Confirm stitching
            </label>

            <div class="flex flex-col space-y-2 mt-2">
              <div
                v-if="hasSpectralData"
                class="flex items-center space-x-2"
              >
                <Checkbox
                  id="include-spectral"
                  v-model:checked="includeSpectral"
                />
                <label
                  for="include-spectral"
                  class="text-sm font-medium leading-none"
                >
                  Include spectral datacube
                </label>
              </div>

              <div
                v-if="hasElementalData"
                class="flex items-center space-x-2"
              >
                <Checkbox
                  id="include-elemental"
                  v-model:checked="includeElemental"
                />
                <label
                  for="include-elemental"
                  class="text-sm font-medium leading-none"
                >
                  Include elemental datacube
                </label>
              </div>
            </div>

            <div class="flex gap-4 justify-center mt-4">
              <Button
                :disabled="!includeSpectral && !includeElemental"
                @click="confirmStitchingDialog"
              >
                Confirm
              </Button>
              <Button variant="outline" @click="closeDialog">
                Cancel
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Window>
</template>

<style scoped>
.dialog-overlay {
  text-align: center;
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
}
.dialog-content {
  text-align: center;
  background: #fff; padding: 2em; border-radius: 8px;
  display: flex;       
  gap: 20px;              
  justify-content: center; 
  align-items: center;  
}
</style>