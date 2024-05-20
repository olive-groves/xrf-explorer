<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ReusableDialog, DialogFooter, DialogClose, DialogTitle } from "@/components/ui/dialog";
import { ref, Ref, computed, inject } from "vue";
import { FrontendConfig } from "@/lib/config";

const config = inject<FrontendConfig>("config")!;
const API_ENDPOINT: string = config.api.endpoint;
const CHUNK_SIZE: number = config.uploadConfig.uploadChunkSizeInBytes;

const uploadedChunks: Ref<number> = ref(0);
const totalChunks: Ref<number> = ref(1);
const uploadProgessPercent: Ref<number> = computed(() => (uploadedChunks.value / totalChunks.value) * 100);

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
  const dataSourceName: string = getTrimmedInputString(dataSourceNameInputRef)!;

  const inputRefsWithFiles = [
    rgbImageInputRef,
    uvImageInputRef,
    xrayImageInputRef,
    cubeDataInputRef,
    rawDataInputRef,
    rplDataInputRef,
  ].filter((inputRef) => getFile(inputRef) !== undefined);

  const errorMsg: string | undefined = validateInputFieds();
  if (errorMsg) {
    alert(errorMsg);
    return;
  }

  totalChunks.value = getTotalChunks(
    inputRefsWithFiles.map((inputRef) => getFile(inputRef)!),
    CHUNK_SIZE,
  );

  const formDataDsName = new FormData();
  formDataDsName.append("name", dataSourceName);

  const response: Response = await fetch(API_ENDPOINT + "/create-ds-dir", {
    method: "POST",
    body: formDataDsName,
  });
  const jsonResponse = await response.json();
  const dataSourceDirName: string = jsonResponse["dataSourceDir"];

  for (const inputRef of inputRefsWithFiles) {
    const file: File = getFile(inputRef)!;
    const uploadFileName: string = generateFileName(inputRef)!;

    const uploadSuccess: boolean = await uploadFileInChunks(file, dataSourceDirName, uploadFileName);

    if (!uploadSuccess) {
      alert("An error has been encountered while uploading.");
      const formDataDelete = new FormData();
      formDataDelete.append("dir", dataSourceDirName);

      fetch(API_ENDPOINT + "/delete-data-source", {
        method: "DELETE",
        body: formDataDelete,
      });

      return;
    }
  }

  const workspaceJSON = generateWorkspaceJSON();
  const workspaceBlob = new Blob([JSON.stringify(workspaceJSON)]);
  const workspaceFile = new File([workspaceBlob], "workspace.json");
  const workspaceUploadedSuccess = await uploadFileInChunks(workspaceFile, dataSourceDirName, "workspace.json");

  if (workspaceUploadedSuccess) {
    alert("Everything uploaded successfully.");
  } else {
    alert("Something went wrong with uploading data source metadata. Otherwise everything's good tho.");
  }
}

/**
 * Splits the given file into chunks and uploads each chunk to the server.
 * @param file - The file to be split and uploaded.
 * @param directory - The directory on the server where the file will be uploaded.
 * @param uploadFileName - The name under which the file will be saved on the server.
 * @returns A promise that resolves to a boolean indicating whether the upload was successful.
 */
async function uploadFileInChunks(file: File, directory: string, uploadFileName: string): Promise<boolean> {
  let uploadSuccess: boolean = true;
  const chunkPromises: Promise<void>[] = [];

  for (let byteIndex = 0; byteIndex < file.size!; byteIndex += CHUNK_SIZE) {
    const chunk: Blob = file!.slice(byteIndex, byteIndex + CHUNK_SIZE);

    const formDataSendChunks = new FormData();
    formDataSendChunks.append("dir", directory + "/" + uploadFileName);
    formDataSendChunks.append("startByte", String(byteIndex));
    formDataSendChunks.append("chunkBytes", chunk);

    const chunkPromise = fetch(API_ENDPOINT + "/upload-file-chunk", {
      method: "POST",
      body: formDataSendChunks,
    }).then((response) => {
      if (!response.ok) {
        uploadSuccess = false;
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
    uploadSuccess = false;
  }

  return uploadSuccess;
}

/**
 * Validates the input fields for a data source upload form.
 * @returns An error message if a validation check fails, otherwise undefined.
 */
function validateInputFieds(): string | undefined {
  if (getTrimmedInputString(dataSourceNameInputRef) === "") {
    return "A non-empty data source name must be provided.";
  }

  if (getFile(rgbImageInputRef) === undefined) {
    return "RGB image must be provided.";
  }

  if (
    (getFile(rawDataInputRef) === undefined && getFile(rplDataInputRef) !== undefined) ||
    (getFile(rawDataInputRef) !== undefined && getFile(rplDataInputRef) === undefined)
  ) {
    return "Both raw and rpl data files must be provided if either one is present.";
  }

  if (
    getFile(cubeDataInputRef) === undefined &&
    (getFile(rawDataInputRef) === undefined || getFile(rplDataInputRef) === undefined)
  ) {
    return "Raw or processed data must be provided.";
  }

  return undefined;
}

/**
 * Returns the type (extension) of the given file, e.g., 'png'.
 * @param file - The file whose type is to be determined.
 * @returns - The file type (extension) without the leading dot.
 */
function getFileType(file: File): string {
  return file.name.split(".").pop()!;
}

/**
 * Generates a json object with metadata about the data source.
 * @returns - An object containing metadata about the data source.
 */
function generateWorkspaceJSON() {
  interface Workspace {
    name: string;
    baseImage: {
      name: string;
      location: string;
    };
    contenxtualImages: { name: string; imageLocation: string; recipeLocation?: string }[];
    spectralCubes: { rawLocation: string; rplLocation: string; recipeLocation?: string }[];
    elementalCubes: { dmsLocation: string; recipeLocation?: string }[];
  }

  const dataSourceName: string = getTrimmedInputString(dataSourceNameInputRef)!;
  const baseImageName: string = getNameAttribute(rgbImageInputRef)!;
  const baseImageLocation: string = `${baseImageName}.${getFileType(getFile(rgbImageInputRef)!)}`;

  const workspace: Workspace = {
    name: dataSourceName,
    baseImage: { name: baseImageName, location: baseImageLocation },
    contenxtualImages: [],
    spectralCubes: [],
    elementalCubes: [],
  };

  if (getFile(uvImageInputRef) !== undefined) {
    workspace.contenxtualImages.push({
      name: getNameAttribute(uvImageInputRef)!,
      imageLocation: generateFileName(uvImageInputRef)!,
    });
  }

  if (getFile(xrayImageInputRef) !== undefined) {
    workspace.contenxtualImages.push({
      name: getNameAttribute(xrayImageInputRef)!,
      imageLocation: generateFileName(xrayImageInputRef)!,
    });
  }

  if (getFile(cubeDataInputRef) !== undefined) {
    workspace.elementalCubes.push({ dmsLocation: generateFileName(cubeDataInputRef)! });
  }

  if (getFile(rawDataInputRef) && getFile(rplDataInputRef)) {
    workspace.spectralCubes.push({
      rawLocation: generateFileName(rawDataInputRef)!,
      rplLocation: generateFileName(rplDataInputRef)!,
    });
  }

  return workspace;
}

/**
 * /**
 * Generates a file name string by combining the name attribute of an input element
 * with the file type of the file selected in that input element.
 * @param inputRef - A reference to an HTML input element.
 * @returns - The generated file name, or undefined if the input reference is invalid.
 */
function generateFileName(inputRef: Ref<HTMLInputElement | undefined>): string | undefined {
  return `${getNameAttribute(inputRef)}.${getFileType(getFile(inputRef)!)}`;
}

/**
 * /**
 * Retrieves the 'name' attribute from an HTML input element reference.
 * @param inputRef - A reference to an HTML input element.
 * @returns - The name attribute of the input element, or undefined if the input reference is invalid.
 */
function getNameAttribute(inputRef: Ref<HTMLInputElement | undefined>): string | undefined {
  return inputRef.value?.name;
}

/**
 * Retrieves the value of an HTML input element, trims any leading or trailing whitespace from it,
 * and returns the trimmed string.
 * @param inputRef - A reference to an HTML input element.
 * @returns - The trimmed value of the input element, or undefined if the input reference is invalid.
 */
function getTrimmedInputString(inputRef: Ref<HTMLInputElement | undefined>): string | undefined {
  return inputRef.value?.value.trim();
}

/**
 * Retrieves the first file from a reference object pointing to a file input element.
 * @param inputRef - A reference to an HTML input element of type file.
 * @returns - The first file selected in the input, or undefined if no files are present.
 */
function getFile(inputRef: Ref<HTMLInputElement | undefined>): File | undefined {
  return inputRef.value?.files![0];
}

/**
 * Calculates the total number of chunks required to upload an array of files.
 * @param files - An array of files to be uploaded.
 * @param chunkSize - The size of each chunk in bytes.
 * @returns - The total number of chunks required to upload the files.
 */
function getTotalChunks(files: File[], chunkSize: number): number {
  let totalBytes = 0;
  files.forEach((file) => {
    totalBytes += file.size;
  });

  return Math.ceil(totalBytes / chunkSize);
}
</script>

<template>
  <ReusableDialog id="upload_file">
    <DialogTitle> Upload files </DialogTitle>

    <div class="flex items-center">
      <label class="w-64">Data source name</label>
      <input
        class="block w-44 rounded-lg bg-accent p-2 text-accent-foreground focus:border-border focus:ring-ring"
        placeholder="Data source"
        type="text"
        ref="dataSourceNameInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">RGB file</label>
      <input
        class="block w-44 cursor-pointer rounded-lg bg-background text-accent-foreground focus:outline-none"
        aria-describedby="rgb_input_help"
        type="file"
        accept=".tiff, .tif, .jpg, .jpeg, .bmp, .png"
        name="rgb"
        ref="rgbImageInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">UV file</label>
      <input
        class="block w-44 cursor-pointer rounded-lg bg-background text-accent-foreground focus:outline-none"
        aria-describedby="uv_input_help"
        type="file"
        accept=".tiff, .tif, .jpg, .jpeg, .bmp, .png"
        name="uv"
        ref="uvImageInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">XRAY file</label>
      <input
        class="block w-44 cursor-pointer rounded-lg bg-background text-accent-foreground focus:outline-none"
        aria-describedby="xray_input_help"
        type="file"
        accept=".tiff, .tif, .jpg, .jpeg, .bmp, .png"
        name="xray"
        ref="xrayImageInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">Cube data</label>
      <input
        class="block w-44 cursor-pointer rounded-lg bg-background text-accent-foreground focus:outline-none"
        aria-describedby="cube_input_help"
        type="file"
        accept=".csv, .dms"
        name="cube"
        ref="cubeDataInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">Raw data (.RAW)</label>
      <input
        class="block w-44 cursor-pointer rounded-lg bg-background text-accent-foreground focus:outline-none"
        aria-describedby="raw_data_input_help"
        type="file"
        accept=".raw"
        name="raw"
        ref="rawDataInputRef"
      />
    </div>
    <div class="flex items-center">
      <label class="w-64">Raw data (.RPL)</label>
      <input
        class="block w-44 cursor-pointer rounded-lg bg-background text-accent-foreground focus:outline-none"
        aria-describedby="raw_data_input_help"
        type="file"
        accept=".rpl"
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
