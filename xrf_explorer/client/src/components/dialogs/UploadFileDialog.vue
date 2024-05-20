<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  ReusableDialog,
  DialogFooter,
  DialogClose,
  DialogTitle,
} from "@/components/ui/dialog";
import { ref, Ref, computed } from "vue";

const CHUNK_SIZE: number = 50000000; // in bytes, therefore 1 MB

const uploadedChunks: Ref<number> = ref(0);
const totalChunks: Ref<number> = ref(1);
const uploadProgessPercent: Ref<number> = computed(
  () => (uploadedChunks.value / totalChunks.value) * 100,
);

const dataSourceNameInputRef = ref<HTMLInputElement>()!;
const rgbImageInputRef = ref<HTMLInputElement>();
const uvImageInputRef = ref<HTMLInputElement>();
const xrayImageInputRef = ref<HTMLInputElement>();
const cubeDataInputRef = ref<HTMLInputElement>();
const rawDataInputRef = ref<HTMLInputElement>();
const rplDataInputRef = ref<HTMLInputElement>();

/**
 * Handles the uploading of data source files to the server.
 * Triggered by the "Upload" button.
 */
async function uploadDataSource() {
  const dataSourceName: string = dataSourceNameInputRef.value?.value.trim()!;

  const inputRefsWithFiles = [
    rgbImageInputRef,
    uvImageInputRef,
    xrayImageInputRef,
    cubeDataInputRef,
    rawDataInputRef,
    rplDataInputRef,
  ].filter((inputRef) => getFile(inputRef) !== undefined);

  if (dataSourceName === "") {
    alert("A non-empty data source name must be provided.");
    return;
  }

  if (getFile(rgbImageInputRef) === undefined) {
    alert("RGB image must be provided.");
    return;
  }

  if (
    getFile(cubeDataInputRef) === undefined &&
    (getFile(rawDataInputRef) === undefined ||
      getFile(rplDataInputRef) === undefined)
  ) {
    alert("Raw or processed data must be provided.");
    return;
  }

  totalChunks.value = getTotalChunks(
    inputRefsWithFiles.map((inputRef) => getFile(inputRef)!),
    CHUNK_SIZE,
  );

  const formDataDsName = new FormData();
  formDataDsName.append("name", dataSourceName);

  let response: Response = await fetch("/api/create-ds-dir", {
    method: "POST",
    body: formDataDsName,
  });
  let jsonResponse = await response.json();
  const dataSourceDirName: string = jsonResponse["dataSourceDir"];

  const chunkPromises: Promise<void>[] = [];
  let abortFileUploading = false;

  for (const inputRef of inputRefsWithFiles) {
    const file: File = getFile(inputRef)!;
    const fileType: string = file.name.split(".").pop()!;
    const uploadFileName: string = inputRef.value?.name + "." + fileType;

    for (let byteIndex = 0; byteIndex < file?.size!; byteIndex += CHUNK_SIZE) {
      const chunk: Blob = file!.slice(byteIndex, byteIndex + CHUNK_SIZE);

      const formDataSendChunks = new FormData();
      formDataSendChunks.append(
        "dir",
        dataSourceDirName + "/" + uploadFileName,
      );
      formDataSendChunks.append("startByte", String(byteIndex));
      formDataSendChunks.append("chunkBytes", chunk);

      const chunkPromise = fetch("/api/upload-file-chunk", {
        method: "POST",
        body: formDataSendChunks,
      }).then((response) => {
        if (!response.ok) {
          abortFileUploading = true;
        } else {
          uploadedChunks.value++;
        }
      });

      chunkPromises.push(chunkPromise);
    }

    try {
      // await all chunk uploads for the current file before proceeding with the next one
      await Promise.all(chunkPromises);
    } catch {
      alert("Network error has occured, please try again later.");
      return;
    }

    if (abortFileUploading) {
      alert("An error has been encountered while uploading.");
      const formDataDelete = new FormData();
      formDataDelete.append("dir", dataSourceDirName);

      fetch("api/delete-data-source", {
        method: "DELETE",
        body: formDataDelete,
      });

      return;
    }
  }
}

/**
 * Retrieves the first file from a ref object pointing to an input element.
 * @returns {File | undefined} The first file selected in the input, or undefined if no files are present.
 */
function getFile(
  inputRef: Ref<HTMLInputElement | undefined>,
): File | undefined {
  return inputRef.value?.files![0];
}

function getTotalChunks(files: File[], chunkSize: number) {
  let totalChunks = 0;
  files.forEach((file) => {
    totalChunks += file.size / chunkSize;
  });

  return Math.ceil(totalChunks);
}
</script>

<template>
  <ReusableDialog id="upload_file">
    <DialogTitle> Upload files </DialogTitle>

    <div class="flex items-center">
      <label class="w-64">Data source name</label>
      <input
        class="bg-accent text-accent-foreground rounded-lg focus:ring-ring focus:border-border block w-44 p-2"
        placeholder="Data source"
        type="text"
        ref="dataSourceNameInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">RGB file</label>
      <input
        class="block w-44 text-accent-foreground rounded-lg cursor-pointer bg-background focus:outline-none"
        aria-describedby="rgb_input_help"
        type="file"
        name="rgb"
        ref="rgbImageInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">UV file</label>
      <input
        class="block w-44 text-accent-foreground rounded-lg cursor-pointer bg-background focus:outline-none"
        aria-describedby="uv_input_help"
        type="file"
        name="uv"
        ref="uvImageInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">XRAY file</label>
      <input
        class="block w-44 text-accent-foreground rounded-lg cursor-pointer bg-background focus:outline-none"
        aria-describedby="xray_input_help"
        type="file"
        name="xray"
        ref="xrayImageInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">Cube data</label>
      <input
        class="block w-44 text-accent-foreground rounded-lg cursor-pointer bg-background focus:outline-none"
        aria-describedby="cube_input_help"
        type="file"
        name="cube"
        ref="cubeDataInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">Raw data (.RAW)</label>
      <input
        class="block w-44 text-accent-foreground rounded-lg cursor-pointer bg-background focus:outline-none"
        aria-describedby="raw_data_input_help"
        type="file"
        name="raw"
        ref="rawDataInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">Raw data (.RPL)</label>
      <input
        class="block w-44 text-accent-foreground rounded-lg cursor-pointer bg-background focus:outline-none"
        aria-describedby="raw_data_input_help"
        type="file"
        name="rpl"
        ref="rplDataInputRef"
      />
    </div>
    <Progress :model-value="uploadProgessPercent" />

    <DialogFooter>
      <DialogClose>
        <Button variant="destructive"> Cancel </Button>
      </DialogClose>
      <Button @click="uploadDataSource">Upload</Button>
    </DialogFooter>
  </ReusableDialog>
</template>
