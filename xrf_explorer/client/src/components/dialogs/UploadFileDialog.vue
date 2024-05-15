<script setup lang="ts">
import { Button } from "@/components/ui/button";
import {
  ReusableDialog,
  DialogFooter,
  DialogClose,
  DialogTitle,
} from "@/components/ui/dialog";
import { ref, Ref } from "vue";

const dataSourceNameInput = ref<HTMLInputElement>()!;
const rgbImageInput = ref<HTMLInputElement>();
const uvImageInput = ref<HTMLInputElement>();
const xrayImageInput = ref<HTMLInputElement>();
const cubeDataInput = ref<HTMLInputElement>();
const rawDataInput = ref<HTMLInputElement>();
const rplDataInput = ref<HTMLInputElement>();

/**
 * Retrieves the first file from a ref object pointing to an input element.
 * @returns {File | undefined} The first file selected in the input, or undefined if no files are present.
 */
function getFile(
  inputRef: Ref<HTMLInputElement | undefined>,
): File | undefined {
  return inputRef.value?.files![0];
}

/**
 * Handles the uploading of data source files to the server.
 * Triggered by the "Upload" button.
 */
function uploadDataSource() {
  const formData = new FormData();

  const dataSourceName: string = dataSourceNameInput.value?.value.trim()!;
  const rgbImageFile = getFile(rgbImageInput);
  const uvImageFile = getFile(uvImageInput);
  const xrayImageFile = getFile(xrayImageInput);
  const cubeDataFile = getFile(cubeDataInput);
  const rawDataFile = getFile(rawDataInput);
  const rplDataFile = getFile(rplDataInput);

  if (dataSourceName === "") {
    alert("A non-empty data source name must be provided.");
    return;
  }

  if (rgbImageFile === undefined) {
    alert("RGB image must be provided.");
    return;
  }

  if (
    cubeDataFile === undefined &&
    (rawDataFile === undefined || rplDataInput === undefined)
  ) {
    alert("Raw or processed data must be provided.");
    return;
  }

  formData.append("name", dataSourceName);
  formData.append("rgb", rgbImageFile);

  // NOTE: This conditional statement assumes that .raw and .rpl files must always be uploaded together. (URF 2.1)
  if (rawDataFile !== undefined && rplDataFile !== undefined) {
    formData.append("raw", rawDataFile);
    formData.append("rpl", rplDataFile);
  }

  if (cubeDataFile !== undefined) {
    formData.append("cube", cubeDataFile);
  }

  if (uvImageFile !== undefined) {
    formData.append("uv", uvImageFile);
  }

  if (xrayImageFile !== undefined) {
    formData.append("xray", xrayImageFile);
  }

  // fetch("/api/upload-source", { method: "POST", body: formData });
}
</script>

<template>
  <ReusableDialog id="upload_file">
    <DialogTitle> Upload files </DialogTitle>

    <div class="flex items-center">
      <!-- TODO: Remove after -->
      <label class="w-64" @click.prevent="test">Data source name</label>
      <input
        type="text"
        class="bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-44 p-2 dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
        placeholder="Data source"
        ref="dataSourceNameInput"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">RGB file</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="rgb_input_help"
        type="file"
        ref="rgbImageInput"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">UV file</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="uv_input_help"
        type="file"
        ref="uvImageInput"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">XRAY file</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="xray_input_help"
        type="file"
        ref="xrayImageInput"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">Cube data</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="cube_input_help"
        type="file"
        ref="cubeDataInput"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">Raw data (.RAW)</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="raw_data_input_help"
        type="file"
        ref="rawDataInput"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">Raw data (.RPL)</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="raw_data_input_help"
        type="file"
        ref="rplDataInput"
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
