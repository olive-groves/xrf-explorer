<script setup lang="ts">
import { deepClone } from "@/lib/utils";
import { kebabCase } from "change-case";
import { computed } from "vue";

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
  /**
   * The unit of the displayed values.
   */
  unit?: string;
}>();

const emit = defineEmits(["update"]);

const defaultValue = props.default ?? deepClone(model.value);

const unit = computed(() => props.unit ?? "");
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
      <Label :for="kebabCase(props.label)">{{ props.label }}</Label>
      <div v-if="model.length == 1" v-text="model[0] + unit" />
      <div v-else-if="model.length == 2" v-text="model[0] + ' – ' + model[1] + unit" />
    </div>
    <Slider
      :id="kebabCase(props.label)"
      v-model="model"
      :min="props.min ?? 0"
      :step="props.step ?? 0.01"
      :max="props.max ?? 1"
      class="cursor-auto pb-2"
      @update:model-value="emit('update')"
    />
  </div>
</template>
