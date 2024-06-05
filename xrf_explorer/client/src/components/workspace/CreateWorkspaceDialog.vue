<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { WorkspaceConfig } from "@/lib/workspace";
import { toast } from "vue-sonner";
import { FileSetupDialog } from ".";
import { TriangleAlert } from "lucide-vue-next";
import { inject, ref, watch } from "vue";
import { FrontendConfig } from "@/lib/config";
import { deepClone } from "@/lib/utils";
import { validateWorkspace } from "./utils";

const config = inject<FrontendConfig>("config")!;

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

const dialogOpen = ref(false);

/**
 * Creates the data source directory in the backend if it does not yet exist with a workspace.json inside.
 */
async function nextStep() {
  if (progress.value == Progress.Name) {
    progress.value = Progress.Busy;
    const name = sourceName.value;

    if (name.trim() == "") {
      progress.value = Progress.Name;
      toast.warning("Data source name must not be empty");
      return;
    }

    // Create the data source directory
    const response = await fetch(`${config.api.endpoint}/${name}/create`, { method: "POST" });

    if (!response.ok) {
      progress.value = Progress.Name;
      toast.error(`Failed to create data source "${name}"`, {
        description: "It might already exist",
      });
      return;
    }

    // Set name in workspace
    workspace.value.name = name;

    progress.value = Progress.Files;
    nextStep();
  } else if (progress.value == Progress.Files) {
    dialogOpen.value = true;
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
async function completeSetup() {
  if (progress.value == Progress.Files) {
    progress.value = Progress.Busy;
    dialogOpen.value = false;
    const workspaceClone = deepClone(workspace.value);

    const validation = validateWorkspace(workspaceClone);
    if (!validation[0]) {
      progress.value = Progress.Files;
      toast.warning("Configured files are not valid", {
        description: validation[1],
      });
      return;
    }

    // Upload the configured workspace.json to the backend
    const response = await fetch(`${config.api.endpoint}/${workspaceClone.name}/workspace`, {
      method: "POST",
      body: JSON.stringify(workspaceClone),
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      progress.value = Progress.Files;
      toast.error("Failed to set up workspace");
      return;
    }

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
    <Input placeholder="Data source name" :disabled="progress != Progress.Name" v-model:model-value="sourceName" />
    <div class="flex items-end justify-between">
      <div class="flex items-center space-x-1.5">
        <TriangleAlert class="size-5 text-primary" />
        <div class="text-muted-foreground">This can not be changed afterwards</div>
      </div>
      <Button @click="nextStep" variant="outline" :disabled="sourceName.trim() == ''" class="ml-2 w-40"> Next </Button>
    </div>
    <Dialog v-model:open="dialogOpen">
      <FileSetupDialog v-model="workspace" @save="completeSetup" />
    </Dialog>
  </DialogContent>
</template>
