<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { LabeledSlider } from "@/components/ui/slider";
import { confirmStitching } from "@/components/image-viewer/stitchHelper";
import { appState } from "@/lib/appState";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { saveWorkspaceDebounced } from "@/components/image-viewer/workspace";

// The current workspace
const workspace = computed(() => appState.workspace);

// Wether the user has selected to include spectral and/or elemental data for stitching
const includeSpectral = ref(false);
const includeElemental = ref(false);

// Wether the workspace contains spectral partial data
const hasSpectralData = computed(() => {
  const ws = appState.workspace;
  return !!(ws && ws.partialSpectralCubes?.length);
});

// Wether the workspace contains elemental partial data
const hasElementalData = computed(() => {
  const ws = appState.workspace;
  return !!(ws && ws.partialElementalCubes?.length);
});

// Wether we are currently displaying the confirm dialog
const showDialog = ref(false);
const showConfirmation = ref(false);

// The opacity of the bade image
const baseImageOpacity = ref([1.0]);

// Current selected scaling factor
const scalingFactor = ref<number[]>([1.0]);

// Optimal size loaded from backend
const estimatedSizeOpt = ref<number | null>(null);

// Optimal percatages data "lost"
const lossesOpt = ref<number[] | null>(null);

// The scaled data lost values based on the selected scaling factor
const scaledLosses = computed(() => {
  if (!lossesOpt.value) return null;

  const factor = scalingFactor.value[0];

  return lossesOpt.value.map((loss) => Math.round(loss * factor * 100) / 100);
});

// The scaled size based on the selected scaling factor
const estimatedSize = computed(() => {
  if (estimatedSizeOpt.value === null) return null;

  const factor = scalingFactor.value[0];
  return Math.round(estimatedSizeOpt.value * factor * factor * 10000) / 10000;
});

// Selected contrast value per greyscale
const grayscaleContrast = ref<number[]>([]);

// The selected opacity and the offset applied to the greyscale
interface GreyscaleState {
  opacity: number[];
  xOffset: number[];
  yOffset: number[];
}
const GreyscaleMapping = ref<GreyscaleState>({
  opacity: [1.0],
  xOffset: [0],
  yOffset: [0],
});

// Update workspace and contrast values when workspace changes
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
  { immediate: true },
);

/**
 * Function to update the contrast values in the workspace.
 * @param idx - The index of the fragment for which the contrast has changed.
 * @param val - The new contrast value.
 */
function updateGreyscaleContrast(idx: number, val: number) {
  grayscaleContrast.value[idx] = val;

  const ws = workspace.value;
  if (ws) {
    ws.mapping.grayscaleContrast[idx] = val;
    saveWorkspaceDebounced();
  }
}

/**
 * Reset contrast values.
 */
function resetContrast() {
  const ws = workspace.value;
  if (!ws) return;
  grayscaleContrast.value = ws.grayscale.map((_, idx) => {
    ws.mapping.grayscaleContrast[idx] = 1.0;
    return 1.0;
  });
  saveWorkspaceDebounced();
}

/**
 * Function to notify the preview viewer about the base opacity change.
 * @param val - The new opacity value.
 */
function updateSliderBase(val: number[]) {
  baseImageOpacity.value = val;
  try {
    const v = Array.isArray(val) ? val[0] : val;
    window.dispatchEvent(new CustomEvent("stitch:base-opacity-changed", { detail: v }));
  } catch (e) {
    console.warn("Could not dispatch stitch base-opacity event", e);
  }
}

/**
 * Function to notify the preview viewer about the greyscale opacity change.
 * @param val - The new opacity value.
 */
function updateGreyscaleOpacity(val: number[]) {
  GreyscaleMapping.value.opacity = val;

  const opacity = val[0];
  window.dispatchEvent(new CustomEvent("stitch:gray-opacity-changed", { detail: opacity }));
}
/**
 * Function to adjust the X-offset by a pixel delta (+1 or -1).
 * @param delta - The amount we need to nudge in the x direction.
 */
function nudgeX(delta: number) {
  window.dispatchEvent(new CustomEvent("stitch:gray-nudge", { detail: { dx: delta, dy: 0 } }));
}

/**
 * Function to adjust the y-offset by a pixel delta (+1 or -1).
 * @param delta - The amount we need to nudge in the y direction.
 */
function nudgeY(delta: number) {
  window.dispatchEvent(new CustomEvent("stitch:gray-nudge", { detail: { dx: 0, dy: delta } }));
}

/**
 * Function to reset the scaling factor.
 */
function resetScaling() {
  scalingFactor.value = [1];
}

/**
 * Function to reset the greyscale offset.
 */
function resetGreyscaleOffset() {
  window.dispatchEvent(new CustomEvent("stitch:reset-offset"));
}

/**
 * Function to close the confirm dialog.
 */
function closeDialog() {
  showDialog.value = false;
  showConfirmation.value = false;
}

/**
 * Function for confirming the stitching.
 */
async function confirmStitchingDialog() {
  closeDialog();
  await confirmStitching(includeSpectral.value, includeElemental.value, scalingFactor.value[0]);
}

/**
 * Function the send preview images to the preview viewer when we go to preview mode.
 * @param e - The event send by the stitch viewer when the mode changes.
 */
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
    }),
  );
}

onMounted(() => {
  window.addEventListener("stitchViewer:stichInfo", onModeChanged as EventListener);
  window.dispatchEvent(new CustomEvent("stitchViewer:requestPreviewInfo"));
});

onBeforeUnmount(() => {
  window.removeEventListener("stitchViewer:stichInfo", onModeChanged as EventListener);
});

/**
 * Function the set the include check boxes based on the available data.
 */
watch(showConfirmation, (open) => {
  if (!open) return;
  includeSpectral.value = hasSpectralData.value;
  includeElemental.value = hasElementalData.value;
});
</script>

<template>
  <Window title="Stitching" location="right">
    <div class="space-y-2 p-2">
      <!-- Slider for base image opacity -->
      <LabeledSlider
        label="Base Image Opacity"
        :model-value="baseImageOpacity"
        :min="0.25"
        :max="1"
        :step="0.01"
        @update:model-value="updateSliderBase"
      />

      <h4 class="font-semibold">{{ `Mapped Data Greyscale` }}</h4>

      <!-- Slider for greyscale opacity -->
      <LabeledSlider
        label="Opacity"
        :model-value="GreyscaleMapping?.opacity ?? [1]"
        :min="0"
        :max="1"
        :step="0.01"
        @update:model-value="updateGreyscaleOpacity"
      />

      <!-- Buttons for changing greyscale offset -->
      <div class="space-y-1">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >X-Offset (pixels)</label
        >
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="nudgeX(-1)">Left</Button>
          <Button size="sm" @click="nudgeX(1)">Right</Button>
        </div>
      </div>

      <div class="space-y-1">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >Y-Offset (pixels)</label
        >
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="nudgeY(-1)">Up</Button>
          <Button size="sm" @click="nudgeY(1)">Down</Button>
        </div>
      </div>

      <!-- Button for reseting offset -->

      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="resetGreyscaleOffset"> Reset offset </Button>
        </div>
      </div>

      <!-- Sliders for changing contrast per fragment -->

      <div v-if="workspace?.grayscale?.length" class="space-y-3 border-t pt-2">
        <h4 class="font-semibold">Contrast</h4>
        <div v-for="(_, idx) in workspace.grayscale" :key="idx" class="space-y-1">
          <label class="text-xs text-foreground">
            {{ workspace.grayscale[idx]?.sourceCubeName ?? `Greyscale ${idx + 1}` }}
          </label>

          <LabeledSlider
            :label="''"
            :model-value="[grayscaleContrast[idx] ?? 1]"
            :min="0.1"
            :max="2"
            :step="0.05"
            @commit="(val: number[]) => updateGreyscaleContrast(idx, val[0])"
          />
        </div>
      </div>

      <!-- Button for reseting contrast -->

      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="resetContrast"> Reset contrast </Button>
        </div>
      </div>

      <!-- Slider for the scaling factor -->

      <LabeledSlider
        label="Scaling Factor"
        :model-value="scalingFactor"
        :min="0.25"
        :max="2"
        :step="0.01"
        @update:model-value="(val: number[]) => (scalingFactor = val)"
      />

      <!-- Button for reseting scaling factor -->

      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <Button size="sm" @click="resetScaling"> Reset scaling </Button>
        </div>
      </div>

      <!-- Display for the preview info -->

      <div class="space-y-1">
        <div>
          <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            Estimated stitched datacube size:
          </label>
          <span>{{ estimatedSize }} GB</span>
        </div>
      </div>
      <div v-if="scaledLosses" class="mt-2 space-y-1 text-sm">
        <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          Estimated percentage of data used per fragment:
        </label>
        <div v-for="(loss, idx) in scaledLosses" :key="idx" class="flex justify-between font-mono">
          <span>{{ workspace?.grayscale[idx]?.sourceCubeName }}</span>
          <span>{{ loss }} %</span>
        </div>
      </div>

      <!-- Confirm button -->

      <Button variant="destructive" class="row-span-3 size-full p-2" @click="showConfirmation = true">
        Confirm Stitching
      </Button>

      <!-- Confirm dialog -->

      <!-- eslint-disable-next-line tailwindcss/no-custom-classname -->
      <div v-if="showConfirmation" class="dialog-overlay">
        <!-- eslint-disable-next-line tailwindcss/no-custom-classname -->
        <div class="dialog-content">
          <div class="flex flex-col space-y-3">
            <label class="text-sm font-medium leading-none"> Confirm stitching </label>

            <div class="mt-2 flex flex-col space-y-2">
              <div v-if="hasSpectralData" class="flex items-center space-x-2">
                <Checkbox id="include-spectral" v-model:checked="includeSpectral" />
                <label for="include-spectral" class="text-sm font-medium leading-none">
                  Include spectral datacube
                </label>
              </div>

              <div v-if="hasElementalData" class="flex items-center space-x-2">
                <Checkbox id="include-elemental" v-model:checked="includeElemental" />
                <label for="include-elemental" class="text-sm font-medium leading-none">
                  Include elemental datacube
                </label>
              </div>
            </div>

            <div class="mt-4 flex justify-center gap-4">
              <Button :disabled="!includeSpectral && !includeElemental" @click="confirmStitchingDialog">
                Confirm
              </Button>
              <Button variant="outline" @click="closeDialog"> Cancel </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Window>
</template>

<!-- Confirm dialog styling -->

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(2px);
}

.dialog-content {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
  padding: 1.5rem;
  border-radius: 0.75rem;
  min-width: 280px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}
</style>
