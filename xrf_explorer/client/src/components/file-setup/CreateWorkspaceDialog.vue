<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Dialog, DialogTrigger, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { WorkspaceConfig } from "@/lib/workspace";
import { computed, ref, watch } from "vue";
import { toast } from "vue-sonner";
import { FileSetupDialog } from ".";
import { validateWorkspace } from "./utils";

const emit = defineEmits(["close"]);

/**
 * Creates a new empty workspace.
 * @returns The new empty workspace.
 */
function createEmptyWorkspace(): WorkspaceConfig {
  return {
    name: "",
    baseImage: {
      imageLocation: "",
      name: "",
      recipeLocation: "",
    },
    contextualImages: [],
    spectralCubes: [],
    elementalCubes: [],
    elementalChannels: [],
  };
}

const workspace = ref(createEmptyWorkspace());

const dialog = ref<HTMLElement>();
watch(dialog, console.log);

enum Progress {
  Name,
  Files,
  Busy,
}

const progress = ref(Progress.Name);

const sourceName = ref("");

const workspaceValid = computed(() => validateWorkspace(workspace.value));

const dialogOpen = ref(false);

/**
 * Creates the data source directory in the backend if it does not yet exist with a workspace.json inside.
 */
async function createDatasource() {
  if (progress.value != Progress.Busy) {
    progress.value = Progress.Busy;
    const name = sourceName.value;

    toast.success(`Created data source ${name}`);
    setTimeout(() => (progress.value = Progress.Files), 1000);
  }
}

/**
 * Resets the progress for creating a new data source.
 */
function resetProgress() {
  if (progress.value != Progress.Busy) {
    progress.value = Progress.Busy;
    emit("close");
    sourceName.value = "";
    workspace.value = createEmptyWorkspace();
    progress.value = Progress.Name;
  }
}

/**
 * Completes setup by saving the initialized workspace.json to the backend.
 */
function completeSetup() {
  if (progress.value != Progress.Busy) {
    progress.value = Progress.Busy;

    toast.success("Created workspace", {
      description: "The created workspace can be opened from the file menu.",
    });

    progress.value = Progress.Files;
    resetProgress();
  }
}
</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Create new data source </DialogTitle>
    <div class="flex space-x-2">
      <Input placeholder="Data source name" :disabled="progress != Progress.Name" v-model:model-value="sourceName" />
      <Button :disabled="progress != Progress.Name" @click="createDatasource()" variant="outline">
        Initialize workspace
      </Button>
    </div>
    <div class="flex justify-between">
      <div>
        <Dialog v-model:open="dialogOpen">
          <DialogTrigger :disabled="progress != Progress.Files">
            <Button :disabled="progress != Progress.Files" variant="outline">Initialize data</Button>
          </DialogTrigger>
          <FileSetupDialog v-model="workspace" @close="dialogOpen = false" />
        </Dialog>
      </div>
      <div class="flex space-x-2">
        <Button :disabled="progress != Progress.Files" variant="destructive" @click="resetProgress">Cancel</Button>
        <Button :disabled="progress != Progress.Files || !workspaceValid[0]" @click="completeSetup"
          >Complete setup</Button
        >
      </div>
    </div>
    <div v-if="!workspaceValid[0] && progress == Progress.Files" class="text-muted-foreground">
      Data must be initialized correctly
    </div>
  </DialogContent>
</template>
