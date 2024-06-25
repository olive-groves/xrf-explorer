<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Dialog, DialogTrigger, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { FrontendConfig } from "@/lib/config";
import { computed, inject, ref } from "vue";
import { toast } from "vue-sonner";

const config = inject<FrontendConfig>("config")!;

const emit = defineEmits(["filesUploaded"]);

const props = defineProps<{
  /**
   * The name of the data source to upload files to.
   */
  dataSource: string;
}>();

const dialogOpen = ref(false);

// Reference to the input component to access the selected files
const inputComponent = ref<InstanceType<typeof Input>>();

// Variables to track the upload progress
const processing = ref(false);
const uploaded = ref(0);
const fileQueue = ref<File[]>([]);
const fileLog = ref<{ file: string; success: boolean }[]>([]);

const currentFile = ref("");
const progressSteps = ref(1);
const progressCompleted = ref(0);
const progress = computed(() => (100 * progressCompleted.value) / progressSteps.value);

/**
 * Upload the configured files to the backend.
 */
function uploadFiles() {
  if (!processing.value) {
    // Reset progress indicator
    fileQueue.value = [];
    uploaded.value = 0;
    fileLog.value = [];
  }

  const input = inputComponent.value?.$el as HTMLInputElement;
  const files = input.files;

  if (files == null) return;

  // Add each selected file to the file queue
  // Loops through the selected files and adds them to the queue for processing.
  for (let i = 0; i < files?.length; i++) {
    fileQueue.value.push(files.item(i)!);
  }

  // Clear the input value
  input.value = "";

  processQueue();
}

/**
 * Start processing items from the queue, uploading them until the queue is empty.
 */
async function processQueue() {
  if (processing.value) return;
  processing.value = true;

  while (fileQueue.value.length > uploaded.value) {
    // Handle single file
    await uploadFile(fileQueue.value[uploaded.value]);
    uploaded.value += 1;

    // Decorative delay
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  processing.value = false;

  toast.info("Finished uploading files");
}

/**
 * Uploads a file.
 * @param file - The file to upload.
 */
async function uploadFile(file: File) {
  // Create an AbortController to handle aborting the upload if needed
  const controller = new AbortController();

  currentFile.value = file.name;
  progressCompleted.value = 0;
  progressSteps.value = Math.ceil(file.size / config.upload.chunkSize);

  const uploads: Promise<void>[] = [];

  // Split the file into chunks and upload each chunk
  for (let i = 0; i < file.size; i += config.upload.chunkSize) {
    const chunk: Blob = file.slice(i, i + config.upload.chunkSize);

    // Upload the chunk to the backend
    const upload = fetch(`${config.api.endpoint}/${props.dataSource}/upload/${file.name}/${i}`, {
      method: "POST",
      body: chunk,
      signal: controller.signal,
    }).then((response) => {
      // If the response is successful (status code 200), update the progress
      if (response.ok) {
        progressCompleted.value += 1;
      } else throw new Error("Chunk upload failed");
    });

    uploads.push(upload);
  }

  try {
    // Wait for all chunk uploads to complete
    await Promise.all(uploads);

    fileLog.value.push({
      file: file.name,
      success: true,
    });
    emit("filesUploaded");
  } catch {
    // Abort the upload if any chunk fails
    controller.abort();

    fileLog.value.push({
      file: file.name,
      success: false,
    });
    toast.error(`Uploading file ${file.name} failed`);
  }
}

/**
 * Updates the state of the dialog.
 * @param open - The new state the dialog is requested to have.
 */
function dialogUpdate(open: boolean) {
  if (open) {
    // Dialog can always be opened
    dialogOpen.value = true;

    // Reset dialog to clean state
    fileLog.value = [];
  } else {
    // Dialog can only be closed if not processing uploads
    if (processing.value) {
      toast.info("Dialog can not be closed while uploading files");
    } else {
      dialogOpen.value = false;
    }
  }
}
</script>

<template>
  <Dialog :open="dialogOpen" @update:open="dialogUpdate">
    <DialogTrigger>
      <Button variant="outline">Upload files</Button>
    </DialogTrigger>
    <DialogContent>
      <div class="max-w-[30rem] space-y-4">
        <!-- HEADER -->
        <DialogTitle class="font-bold">Upload files</DialogTitle>

        <!-- FILE SELECTION -->
        <div class="flex space-x-2">
          <Input ref="inputComponent" type="file" multiple />
          <Button @click="uploadFiles">Upload files</Button>
        </div>

        <!-- PROGRESS VISUALIZATION -->
        <div class="space-y-1.5" v-if="processing">
          <div class="flex justify-between">
            <Label>Uploading {{ currentFile }}</Label>
            <Label>{{ uploaded }}/{{ fileQueue.length }}</Label>
          </div>
          <Progress v-model="progress" />
        </div>

        <!-- LOG MESSAGES -->
        <div v-if="fileLog.length > 0">
          <div
            v-for="log in fileLog"
            :key="log.file"
            v-text="log.success ? `Uploaded ${log.file}` : `Failed to upload ${log.file}`"
            class="text-xs"
            :class="{
              'text-muted-foreground': log.success,
              'text-red-600': !log.success,
            }"
          />
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>
