<script setup lang="ts">
import { Checkbox } from "@/components/ui/checkbox";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { FrontendConfig } from "@/lib/config";
import { inject, ref, toRef } from "vue";
import { toast } from "vue-sonner";

const config = inject<FrontendConfig>("config")!;

const props = defineProps<{
  /**
   * The name of the datasource to delete.
   */
  name: string;
}>();

const emit = defineEmits(["close"]);

const name = toRef(props, "name");

const deleteFiles = ref(false);

/**
 * Deletes the workspace.
 */
async function deleteWorkspace() {
  const url = deleteFiles.value
    ? `${config.api.endpoint}/${name.value}/delete`
    : `${config.api.endpoint}/${name.value}/remove`;
  const method = deleteFiles.value ? "DELETE" : "POST";

  const response = await fetch(url, { method: method });

  if (response.ok) {
    toast.success("Deleted project", { description: "Please reload the page" });
    emit("close");
  } else {
    toast.error("An error occurred while deleting project");
  }
}
</script>

<template>
  <DialogContent>
    <DialogTitle>Delete project</DialogTitle>
    <div>
      By default only the XRF-Explorer configuration will be removed when deleting a project. By checking the checkbox
      all associated data files will also be removed, make sure that this is not the only copy of the data files before
      deleting. Deletion can not be undone. Non deleted files can be reused by recreating a project with the name '{{
        name
      }}'.
    </div>
    <div class="flex items-center justify-between">
      <div class="flex space-x-2">
        <Checkbox v-model:checked="deleteFiles" id="delete_files" />
        <Label for="delete_files">Also delete all associated files</Label>
      </div>
      <div class="flex space-x-2">
        <Button @click="deleteWorkspace" variant="destructive">Delete</Button>
        <Button @click="emit('close')">Cancel</Button>
      </div>
    </div>
  </DialogContent>
</template>
