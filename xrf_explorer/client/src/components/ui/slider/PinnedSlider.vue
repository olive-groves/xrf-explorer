<script setup lang="ts">
import { deepClone } from "@/lib/utils";

const model = defineModel<number[]>({ required: true });

const props = defineProps<{
  /**
   * The optional default value of the slider.
   */
  default?: number[];
  /**
   * The minimum value of the slider.
   */
  min?: number;
  /**
   * The maximum value of the slider.
   */
  max?: number;
  /**
   * The step size of the slider.
   */
  step?: number;
  /**
   * The unit of the displayed values.
   */
  unit?: string;
}>();

const emit = defineEmits(["update"]);

const defaultValue = props.default ?? deepClone(model.value);

</script>

<template>
  <div
    class="space-y-2"
    @dblclick="
      () => {
        model = deepClone(defaultValue);
        emit('update');
      }
    "
  >
    <Slider
      v-model="model"
      :min="props.min ?? 0"
      :step="props.step ?? 0.01"
      :max="props.max ?? 1"
      class="cursor-auto pb-2"
      @update:model-value="emit('update')"
    />
  </div>
</template>
