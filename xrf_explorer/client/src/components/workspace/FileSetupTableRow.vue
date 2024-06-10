<script setup lang="ts">
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";

const model = defineModel<string>();

const props = defineProps<{
  /**
   * List of possible filenames.
   */
  options: string[];
  /**
   * Will be used in the select placeholder to indicate the type.
   */
  type: string;
}>();
</script>

<template>
  <div class="col-start-3 w-full">
    <Select v-model:model-value="model">
      <SelectTrigger>
        <SelectValue :placeholder="`Select ${props.type} file`" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem v-if="props.options.length == 0" disabled value="disabled">No valid files present</SelectItem>
        <SelectItem v-for="option in props.options" :key="option" :value="option">{{ option }}</SelectItem>
      </SelectContent>
    </Select>
  </div>
</template>
