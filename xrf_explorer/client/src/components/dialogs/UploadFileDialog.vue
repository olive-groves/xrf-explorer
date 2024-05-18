<script setup lang="ts">
import { Button } from "@/components/ui/button";
import {
  ReusableDialog,
  DialogFooter,
  DialogClose,
  DialogTitle,
} from "@/components/ui/dialog";
import { ref, Ref } from "vue";

/**
 * Retrieves the first file from a ref object pointing to an input element.
 * @returns {File | undefined} The first file selected in the input, or undefined if no files are present.
 */
function getFile(
  inputRef: Ref<HTMLInputElement | undefined>,
): File | undefined {
  return inputRef.value?.files![0];
}

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
  ].filter((input) => input.value?.files![0] !== undefined);

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

  const formDataDsName = new FormData();
  formDataDsName.append("name", dataSourceName);

  let response: Response = await fetch("/api/create-ds-dir", {
    method: "POST",
    body: formDataDsName,
  });
  let jsonResponse = await response.json();
  const dataSourceDirName: string = jsonResponse["dataSourceDir"];

  console.log("The name of the data source dir is " + dataSourceDirName);
  console.log("The input refs which have files are " + inputRefsWithFiles);

  inputRefsWithFiles.forEach((inputRef) => {
    const file: File = getFile(inputRef)!;
    const fileType: string = file.name.split(".").pop()!;
    const uploadFileName = inputRef.value?.name + "." + fileType;
    const chunkSize = 3000000 / 2; // in bytes, therefore 1 MB

    for (let byteIndex = 0; byteIndex < file?.size!; byteIndex += chunkSize) {
      const chunk: Blob = file!.slice(byteIndex, byteIndex + chunkSize);

      const formDataSendChunks = new FormData();
      formDataSendChunks.append(
        "dir",
        dataSourceDirName + "/" + uploadFileName,
      );
      formDataSendChunks.append("startByte", String(byteIndex));
      formDataSendChunks.append("chunkBytes", chunk);

      fetch("/api/upload-file-chunk", {
        method: "POST",
        body: formDataSendChunks,
      });
    }
  });
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

    <DialogFooter>
      <DialogClose>
        <Button variant="destructive"> Cancel </Button>
      </DialogClose>
      <Button @click="uploadDataSource">Upload</Button>
    </DialogFooter>
  </ReusableDialog>
</template>
