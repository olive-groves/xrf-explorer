<script setup lang="ts">
import { Button } from "@/components/ui/button";
import {
  ReusableDialog,
  DialogFooter,
  DialogClose,
  DialogTitle,
} from "@/components/ui/dialog";
import { FileInput } from "@/components/ui/file-upload";
</script>

<template>
  <ReusableDialog id="upload_file">
    <DialogTitle> Upload files </DialogTitle>

    <div class="flex items-center">
      <label for="data_source_name" class="w-64">Data source name</label>
      <input
        type="text"
        id="data_source_name"
        class="bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-44 p-2 dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
        placeholder="Data source"
        required
      />
    </div>
    <div class="flex items-center">
      <label class="w-64" for="rgb_input">RGB file</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="rgb_input_help"
        id="rgb_input"
        type="file"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64" for="uv_input">UV file</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="uv_input_help"
        id="uv_input"
        type="file"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64" for="xray_input">XRAY file</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="xray_input_help"
        id="xray_input"
        type="file"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64" for="cube_input">Cube data</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="cube_input_help"
        id="cube_input"
        type="file"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64" for="raw_data_input">Raw data</label>
      <input
        class="block w-44 text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-900 dark:border-gray-700 dark:placeholder-gray-400"
        aria-describedby="raw_data_input_help"
        id="raw_data_input"
        type="file"
      />
    </div>

    <DialogFooter>
      <DialogClose>
        <Button variant="destructive"> Cancel </Button>
      </DialogClose>
      <Button>Upload</Button>
    </DialogFooter>
  </ReusableDialog>
</template>

