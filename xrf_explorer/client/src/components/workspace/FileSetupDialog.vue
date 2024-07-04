<script setup lang="ts">
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { AdditionalSettingsDialog, FileSetupTable } from ".";
import { WorkspaceConfig } from "@/lib/workspace";
import { validateWorkspace } from "./utils";
import { computed } from "vue";
import { TriangleAlert } from "lucide-vue-next";

// Define the workspace model
const model = defineModel<WorkspaceConfig>({ required: true });

// Define the save event
const emit = defineEmits(["save"]);

const modelValidity = computed(() => validateWorkspace(model.value));

/**
 * Emit the save event, thus prompting the containing element to save the updated setup.
 */
function save() {
  emit("save");
}
</script>

<template>
  <DialogContent class="max-w-fit">
    <div class="w-[48rem] space-y-4">
      <!-- Header -->
      <DialogTitle class="font-bold">Set up workspace data</DialogTitle>

      <!-- Content -->
      <FileSetupTable v-model="model" />

      <!-- Footer -->
      <div class="flex justify-between">
        <div class="flex items-center space-x-1.5">
          <TriangleAlert v-if="!modelValidity[0]" class="size-5 text-primary" />
          <div class="text-muted-foreground" v-text="modelValidity[1]" />
        </div>
        <div class="space-x-2">
          <AdditionalSettingsDialog v-model="model" />
          <Button :disabled="!modelValidity[0]" @click="save" :title="modelValidity[1]">Save</Button>
        </div>
      </div>
    </div>
  </DialogContent>
</template>
