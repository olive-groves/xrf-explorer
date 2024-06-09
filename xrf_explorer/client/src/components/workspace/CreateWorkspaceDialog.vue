<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { WorkspaceConfig } from "@/lib/workspace";
import { toast } from "vue-sonner";
import { ChannelSetupDialog, FileSetupDialog } from ".";
import { TriangleAlert } from "lucide-vue-next";
import { inject, ref, watch } from "vue";
import { FrontendConfig } from "@/lib/config";
import { deepClone } from "@/lib/utils";
import { initializeChannels, validateWorkspace } from "./utils";

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

// Progress state of the setup process
enum Progress {
  Name,
  Files,
  Channels,
  Finished,
  Busy,
}

const progress = ref(Progress.Name);

// Data source name
const sourceName = ref("");

// Dialogs for file and channel setup
const fileDialog = ref(false);
const channelDialog = ref(false);

/**
 * Creates the data source directory in the backend if it does not yet exist with a workspace.json inside.
 */
async function initializeDataSource() {
  if (progress.value == Progress.Name) {
    progress.value = Progress.Busy;
    const name = sourceName.value;

    // Check if the name is empty
    if (name.trim() == "") {
      progress.value = Progress.Name;
      toast.warning("Data source name must not be empty");
      return;
    }

    // Create the data source directory
    const response = await fetch(`${config.api.endpoint}/${name}/create`, { method: "POST" });

    // Check if the request was successful
    if (!response.ok) {
      progress.value = Progress.Name;
      toast.error(`Failed to create data source "${name}"`, {
        description: "It might already exist",
      });
      return;
    }

    // Set name in workspace
    workspace.value.name = name;

    // Move to the next step
    progress.value = Progress.Files;
    initializeDataSource();
  } else if (progress.value == Progress.Files) {
    fileDialog.value = true;
  } else if (progress.value == Progress.Channels) {
    channelDialog.value = true;
  }
}

/**
 * Resets the progress for creating a new data source.
 */
function resetProgress() {
  progress.value = Progress.Busy;
  emit("close");
  sourceName.value = "";
  workspace.value = createEmptyWorkspace();
  progress.value = Progress.Name;
}

/**
 * Completes setup by saving the initialized workspace.json to the backend.
 * @returns - Whether setup was successfull.
 */
async function setupWorkspace(): Promise<boolean> {
  fileDialog.value = false;
  channelDialog.value = false;
  const workspaceClone = deepClone(workspace.value);

  // Validate the configured files
  const validation = validateWorkspace(workspaceClone);
  if (!validation[0]) {
    toast.warning("Configured files are not valid", {
      description: validation[1],
    });
    return false;
  }

  // Upload the configured workspace.json to the backend
  const response = await fetch(`${config.api.endpoint}/${workspaceClone.name}/workspace`, {
    method: "POST",
    body: JSON.stringify(workspaceClone),
    headers: {
      "Content-Type": "application/json",
    },
  });

  // Inform the if the request was not successful
  if (!response.ok) {
    toast.error("Failed to set up workspace");
    return false;
  }

  return true;
}

/**
 * Creates the workspace on the backend if setup is complete.
 */
async function updateWorkspace() {
  if (progress.value != Progress.Busy) {
    progress.value = Progress.Busy;

    const setup = await setupWorkspace();

    if (workspace.value.elementalCubes.length > 0 && workspace.value.elementalChannels.length == 0) {
      // Elemental channels need to get set up
      const initialized = initializeChannels(workspace.value);

      // Check if the channels can be initialized
      if (!initialized) {
        progress.value = Progress.Files;
        toast.error("Failed to initialize elemental channels", {
          description: "The elemental cube might be configured with an incorrect or malformed data file",
        });
        return;
      }

      // Move to the next step
      progress.value = Progress.Channels;
      fileDialog.value = false;
      channelDialog.value = true;
    } else if (setup) {
      // Complete setup
      toast.success("Created workspace", {
        description: "The created workspace can be opened from the file menu.",
      });

      resetProgress();
    }
  }
}
</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Create new data source </DialogTitle>
    <Input placeholder="Data source name" :disabled="progress != Progress.Name" v-model:model-value="sourceName" />
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-1.5" v-if="progress == Progress.Name">
        <TriangleAlert class="size-5 text-primary" />
        <div class="text-muted-foreground">This can not be changed afterwards</div>
      </div>
      <Button @click="resetProgress" variant="destructive" v-else-if="progress == Progress.Files">Abort</Button>
      <Button @click="updateWorkspace" variant="outline" v-else-if="progress == Progress.Channels">
        Skip channel setup
      </Button>
      <div v-else />
      <Button @click="initializeDataSource" :disabled="progress == Progress.Busy || sourceName.trim() == ''">{{
        progress == Progress.Channels ? "Channel setup" : "Next"
      }}</Button>
    </div>
    <Dialog v-model:open="fileDialog">
      <FileSetupDialog v-model="workspace" @save="updateWorkspace" />
    </Dialog>
    <Dialog v-model:open="channelDialog">
      <ChannelSetupDialog v-model="workspace" @save="updateWorkspace" />
    </Dialog>
  </DialogContent>
</template>
