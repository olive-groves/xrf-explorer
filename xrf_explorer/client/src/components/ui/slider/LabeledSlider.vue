<script setup lang="ts">
import { deepClone } from "@/lib/utils";

const model = defineModel<number[]>({ required: true });

const props = defineProps<{
  /**
   * The label to use above the slider.
   */
  label: string;
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
   * The stepsize of the slider.
   */
  step?: number;
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
    <div class="flex items-center justify-between">
      <div v-text="props.label"></div>
      <div v-if="model.length == 1" v-text="model[0]" />
      <div v-else-if="model.length == 2" v-text="model[0] + ' – ' + model[1]" />
    </div>
    <Slider
      v-model="model"
      :min="props.min ?? 0"
      :step="props.step ?? 0.01"
      :max="props.max ?? 1"
      class="pb-2"
      @update:model-value="emit('update')"
    />
  </div>
</template>
