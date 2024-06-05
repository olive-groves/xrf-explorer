<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogScrollContent, DialogTitle } from "@/components/ui/dialog";
import { FileSetupTable } from ".";
import { WorkspaceConfig } from "@/lib/workspace";
import { validateWorkspace } from "./utils";
import { computed } from "vue";
import { TriangleAlert } from "lucide-vue-next";

const model = defineModel<WorkspaceConfig>({ required: true });

const emit = defineEmits(["close", "save"]);

const modelValid = computed(() => validateWorkspace(model.value));

/**
 * Emit the save event, prompting the containing element to save the updated setup.
 */
function save() {
  emit("save");
  close();
}

/**
 * Emit the close event, instructing the containing element to close the dialog.
 */
function close() {
  emit("close");
}
</script>

<template>
  <DialogScrollContent class="max-w-fit">
    <div class="w-[48rem] space-y-4">
      <DialogTitle class="font-bold">Set up workspace data</DialogTitle>
      <FileSetupTable v-model="model" />
      <div class="flex justify-between">
        <div class="flex items-end space-x-1.5">
          <TriangleAlert v-if="!modelValid[0]" class="size-5 text-primary" />
          <div class="text-muted-foreground" v-text="modelValid[1]" />
        </div>
        <div class="space-x-2">
          <Button variant="outline" @click="close">Close</Button>
          <Button :disabled="!modelValid[0]" @click="save">Save</Button>
        </div>
      </div>
    </div>
  </DialogScrollContent>
</template>
