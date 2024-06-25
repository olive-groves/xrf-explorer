<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { WorkspaceConfig } from "@/lib/workspace";
import { toast } from "vue-sonner";
import { ChannelSetupDialog, ExistingFilesDialog, FileSetupDialog } from ".";
import { TriangleAlert } from "lucide-vue-next";
import { inject, ref } from "vue";
import { FrontendConfig } from "@/lib/config";
import { deepClone } from "@/lib/utils";
import { initializeChannels, validateWorkspace } from "./utils";
import { appState } from "@/lib/appState";

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
    spectralParams: {
      low: 0,
      high: 40,
      binSize: 1,
      binned: false,
    },
  };
}

const workspace = ref(createEmptyWorkspace());

// Progress state of the setup process
enum Progress {
  Name,
  ExistingFiles,
  Files,
  Channels,
  Finished,
  Busy,
}

const progress = ref(Progress.Name);

// Data source name
const sourceName = ref("");

// Dialogs for file and channel setup
const existingFilesDialog = ref(false);
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
      toast.warning("Project name must not be empty");
      return;
    }
    // Create the data source directory
    const response = await fetch(`${config.api.endpoint}/${name}/create`, { method: "POST" });

    // Check if the request was successful
    if (!response.ok) {
      progress.value = Progress.Name;
      toast.error(`Failed to create project "${name}"`, {
        description: "The project might already exist",
      });
      return;
    }
    // Set name in workspace
    workspace.value.name = name;

    // Check if workspace already contains files
    const filesResponse = await fetch(`${config.api.endpoint}/${name}/files`);
    const files = (await filesResponse.json()) as string[];
    if (files.length > 0) {
      // Open the existing files dialog
      progress.value = Progress.ExistingFiles;
    } else {
      // Move to the next step
      progress.value = Progress.Files;
    }
    initializeDataSource();
  } else if (progress.value == Progress.ExistingFiles) {
    existingFilesDialog.value = true;
  } else if (progress.value == Progress.Files) {
    fileDialog.value = true;
  } else if (progress.value == Progress.Channels) {
    channelDialog.value = true;
  }
}

/**
 * Moves progress to files step after checking out existing files.
 */
function closedExistingFilesDialog() {
  if (existingFilesDialog.value) return;

  progress.value = Progress.Files;
  initializeDataSource();
}

/**
 * Handles starting the next step after removing existing files.
 */
function deletedExistingFiles() {
  existingFilesDialog.value = false;
  progress.value = Progress.Files;
  initializeDataSource();
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
 * Remove workspace.json in the backend if it exists.
 */
async function abortDataSourceCreation() {
  const name = workspace.value.name;
  try {
    const response = await fetch(`${config.api.endpoint}/${name}/remove`, { method: "POST" });

    if (response.ok) {
      const data = await response.json();
      console.info(`Data source directory removed: ${data.dataSourceDir}`);
    } else {
      const error = await response.text();
      console.error(`Error removing data source directory: ${error}`);
    }
  } catch (error) {
    console.error(`An error occurred: ${error}`);
  }

  resetProgress();
}

/**
 * Completes setup by saving the initialized workspace.json to the backend.
 * @returns - Whether setup was successful.
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

  // Inform the user if the request was not successful
  if (!response.ok) {
    toast.error("Failed to set up workspace");
    return false;
  }

  return true;
}

/**
 * Creates the workspace on the backend if setup is complete.
 * @returns - Whether the update was successful.
 */
async function updateWorkspace() {
  if (progress.value != Progress.Busy) {
    progress.value = Progress.Busy;
    const setup = await setupWorkspace();

    // Convert elemental data cube to .dms format if necessary
    const aNonDmsFile = workspace.value.elementalCubes.some((cubeInfo) => {
      if (!cubeInfo.dataLocation.endsWith(".dms")) {
        return true;
      }
    });

    if (aNonDmsFile) {
      // Convert elemental data cube to .dms format
      await convertCubeToDms();

      // Update workspace with the new data location
      workspace.value.elementalCubes.forEach((cubeInfo) => {
        cubeInfo.dataLocation = cubeInfo.dataLocation.split(".").slice(0, -1).join(".") + ".dms";
      });
    }

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
      binData();
      // Complete setup
      toast.success("Created workspace", {
        description: "The created workspace can be opened from the file menu.",
      });
      resetProgress();
    }
  }
}

/**
 * Converts the elemental data cube to .dms format.
 */
async function convertCubeToDms() {
  console.info(`Converting elemental data cube.`);
  // Convert elemental data cube
  await fetch(`${config.api.endpoint}/${workspace.value.name}/data/convert`).then((response) => {
    if (!response.ok) {
      throw new Error("Conversion failed");
    }
  });
}

/**
 * Bins the updated raw data.
 */
async function binData() {
  // Bin raw data
  await fetch(`${config.api.endpoint}/${workspace.value.name}/bin_raw/`, {
    method: "POST",
  }).then((response) => {
    // If the response is successful (status code 200), update the progress
    if (response.ok) {
      // If a workspace is already loaded, update binned in the app state
      if (typeof appState.workspace !== "undefined") {
        appState.workspace.spectralParams.binned = true;
      }
      workspace.value.spectralParams.binned = true;
    } else throw new Error("Binning failed");
  });
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
      <Button @click="abortDataSourceCreation" variant="destructive" v-else-if="progress == Progress.Files">
        Abort
      </Button>
      <Button @click="updateWorkspace" variant="outline" v-else-if="progress == Progress.Channels">
        Skip channel setup
      </Button>
      <div v-else />
      <Button @click="initializeDataSource" :disabled="progress == Progress.Busy || sourceName.trim() == ''">{{
        progress == Progress.Channels ? "Channel setup" : "Next"
      }}</Button>
    </div>
    <Dialog v-model:open="existingFilesDialog" @update:open="closedExistingFilesDialog">
      <ExistingFilesDialog :name="workspace.name" @deleted="deletedExistingFiles" />
    </Dialog>
    <Dialog v-model:open="fileDialog">
      <FileSetupDialog v-model="workspace" @save="updateWorkspace" />
    </Dialog>
    <Dialog v-model:open="channelDialog">
      <ChannelSetupDialog v-model="workspace" @save="updateWorkspace" />
    </Dialog>
  </DialogContent>
</template>
