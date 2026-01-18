<script setup lang="ts">
import { inject } from "vue";
import { FileSetupTableRow, FileUploadDialog } from ".";
import { Image, AudioWaveform, Atom, Trash2 } from "lucide-vue-next";
import { ScrollArea } from "../ui/scroll-area";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { WorkspaceConfig } from "@/lib/workspace";
import { FrontendConfig } from "@/lib/config";
import {
  useFileSetupTable,
  UploadingPartialData,
  includeSpectral,
  includeElemental,
  showDeleteComponentDialog,
  showMultiDeleteDialog,
  showDeleteFileDialog,
  selectedFilesToDelete,
  componentNameToDelete,
} from "./FileSetupTable";

const config = inject<FrontendConfig>("config")!;
const model = defineModel<WorkspaceConfig>({ required: true });

const {
  fileFetch,
  imageFiles,
  recipeFiles,
  rawFiles,
  rplFiles,
  elementalFiles,
  allProjectFiles,
  spectralArr,
  elementalArr,
  maxCubes,
  addDatacube,
  canDeleteFragment,
  removeComponentsFromWorkspace,
  addContextualImage,
  removeContextualImage,
  handleMultiDeleteConfirmed,
} = useFileSetupTable(model, config);

defineExpose({ getUploadingPartialData: () => UploadingPartialData.value });
</script>

<template>
  <div>
    <!-- Header -->
    <div class="grid grid-cols-[2rem,12rem,1fr,2rem] place-items-center gap-2">
      <div class="col-start-2 place-self-start">Name</div>
      <div class="col-start-3 place-self-start">Files</div>
    </div>
    <Separator class="mt-2" />

    <!-- Scroll area -->
    <ScrollArea class="mr-[-0.8125rem] h-[32rem] pr-[0.8125rem]">
      <div class="grid grid-cols-[2rem,12rem,1fr,2rem] place-items-center gap-2 pt-2">
        <!-- Base image -->
        <div class="col-span-full mb-1 justify-self-start text-sm font-medium text-gray-500">Base image</div>
        <Image class="ml-2 size-6" title="Base image" />
        <Input placeholder="Name" v-model:model-value="model.baseImage.name" />
        <FileSetupTableRow type="an image" :options="imageFiles" v-model="model.baseImage.imageLocation" />
        <Separator class="col-span-full" />

        <!-- Fragments -->
        <template v-for="index in maxCubes" :key="index">
          <template v-if="includeElemental || includeSpectral">
            <div class="col-span-full mb-2 mt-4 justify-self-start text-lg font-semibold">Fragment {{ index }}</div>

            <!-- Spectral -->
            <div v-if="includeSpectral && spectralArr[index - 1]" class="col-span-full grid grid-cols-subgrid gap-2">
              <div class="col-span-full mb-1 text-sm font-medium text-gray-500">Spectral Datacube</div>
              <AudioWaveform class="ml-2 size-6" />
              <Input placeholder="Name" v-model:model-value="spectralArr[index - 1].name" />
              <FileSetupTableRow type="a raw" :options="rawFiles" v-model="spectralArr[index - 1].rawLocation" />
              <FileSetupTableRow type="an rpl" :options="rplFiles" v-model="spectralArr[index - 1].rplLocation" />
              <FileSetupTableRow
                v-if="UploadingPartialData === 'full'"
                type="a recipe"
                :options="recipeFiles"
                v-model="spectralArr[index - 1].recipeLocation"
              />
            </div>

            <!-- Elemental -->
            <div v-if="includeElemental && elementalArr[index - 1]" class="col-span-full grid grid-cols-subgrid gap-2">
              <div class="col-span-full mb-1 text-sm font-medium text-gray-500">Elemental Datacube</div>
              <Atom class="ml-2 size-6" />
              <Input placeholder="Name" v-model:model-value="elementalArr[index - 1].name" />
              <FileSetupTableRow
                type="a data"
                :options="elementalFiles"
                v-model="elementalArr[index - 1].dataLocation"
              />
              <FileSetupTableRow
                v-if="UploadingPartialData === 'full'"
                type="a recipe"
                :options="recipeFiles"
                v-model="elementalArr[index - 1].recipeLocation"
              />
            </div>

            <!-- Fragment delete button -->
            <Button
              v-if="(spectralArr[index - 1] || elementalArr[index - 1]) && canDeleteFragment(index)"
              variant="destructive"
              class="col-span-full my-2"
              @click="
                componentNameToDelete = index;
                showDeleteComponentDialog = true;
              "
            >
              <Trash2 /> Delete Fragment
            </Button>

            <Separator class="col-span-full mt-2" />
          </template>
        </template>

        <!-- Contextual images -->
        <div
          v-if="model.contextualImages.length > 0"
          class="col-span-full mb-2 mt-4 justify-self-start text-lg font-semibold"
        >
          Contextual images
        </div>

        <template v-for="(image, index) in model.contextualImages" :key="index">
          <div class="col-span-full grid grid-cols-subgrid gap-2">
            <Image class="ml-2 size-6" title="Contextual image" />

            <Input placeholder="Name" v-model:model-value="image.name" />

            <FileSetupTableRow type="an image" :options="imageFiles" v-model="image.imageLocation" />

            <FileSetupTableRow type="a recipe" :options="recipeFiles" v-model="image.recipeLocation" />

            <Button
              variant="destructive"
              class="row-span-2 size-full p-2"
              @click="removeContextualImage(index)"
              title="Remove contextual image"
            >
              <Trash2 />
            </Button>
          </div>

          <Separator class="col-span-full my-2" />
        </template>

        <!-- Delete component dialog -->
        <div v-if="showDeleteComponentDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div class="min-w-[320px] rounded-lg bg-background p-6 text-foreground shadow-lg">
            <div class="mb-2 text-lg font-bold">Confirm Deletion</div>
            <div class="mb-4 text-sm text-muted-foreground">
              Are you sure you want to delete this component from the workspace? This action cannot be undone.
            </div>
            <div class="flex justify-end space-x-2">
              <Button variant="outline" @click="showDeleteComponentDialog = false">Cancel</Button>
              <Button variant="destructive" @click="removeComponentsFromWorkspace(componentNameToDelete)"
                >Delete</Button
              >
            </div>
          </div>
        </div>
      </div>
    </ScrollArea>

    <!-- Footer -->
    <div class="mt-2 flex w-full items-start justify-between">
      <div class="flex flex-col space-y-2">
        <ToggleGroup type="single" v-model="UploadingPartialData" class="space-x-2">
          <ToggleGroupItem value="full" variant="outline">Full data scan</ToggleGroupItem>
          <ToggleGroupItem value="partial" variant="outline">Partial data scans</ToggleGroupItem>
        </ToggleGroup>

        <div class="mt-2 flex flex-col space-y-2">
          <div class="flex items-center space-x-2">
            <Checkbox id="include-spectral" v-model:checked="includeSpectral" />
            <label for="include-spectral" class="text-sm font-medium leading-none">Include spectral datacube</label>
          </div>
          <div class="flex items-center space-x-2">
            <Checkbox id="include-elemental" v-model:checked="includeElemental" />
            <label for="include-elemental" class="text-sm font-medium leading-none">Include elemental datacube</label>
          </div>
        </div>
      </div>

      <div class="flex items-start space-x-4">
        <!-- Add actions -->
        <div class="flex flex-col space-y-2">
          <Button v-if="UploadingPartialData === 'partial'" variant="outline" @click="addDatacube">
            Add partial data cube
          </Button>

          <Button variant="outline" @click="addContextualImage"> Add contextual image </Button>
        </div>

        <!-- File actions -->
        <div class="flex flex-col space-y-2">
          <FileUploadDialog :data-source="model.name" @files-uploaded="fileFetch.execute()" />

          <Button variant="destructive" @click="showMultiDeleteDialog = true"> Delete Files </Button>
        </div>
      </div>
    </div>

    <!-- Multi-delete dialog -->
    <div v-if="showMultiDeleteDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="max-h-[500px] min-w-[360px] overflow-y-auto rounded-lg bg-background p-6 shadow-lg">
        <div class="mb-2 text-lg font-bold">Delete Files</div>
        <div class="mb-4 text-sm">Select the files you want to delete from this project.</div>
        <div class="mb-4 space-y-2">
          <label v-for="file in allProjectFiles" :key="file" class="flex items-center space-x-2">
            <input type="checkbox" :value="file" v-model="selectedFilesToDelete" class="" />
            <span class="truncate">{{ file }}</span>
          </label>
        </div>
        <div class="flex justify-end space-x-2">
          <Button variant="outline" @click="showMultiDeleteDialog = false">Cancel</Button>
          <Button
            variant="destructive"
            :disabled="selectedFilesToDelete.length === 0"
            @click="showDeleteFileDialog = true"
            >Delete Selected</Button
          >
        </div>
      </div>
    </div>

    <!-- Delete files confirmation -->
    <div v-if="showDeleteFileDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="min-w-[320px] rounded-lg bg-background p-6 shadow-lg">
        <div class="mb-2 text-lg font-bold">Confirm Deletion</div>
        <div class="mb-4 text-sm">Are you sure you want to delete these files? This action cannot be undone.</div>
        <div class="flex justify-end space-x-2">
          <Button variant="outline" @click="showDeleteFileDialog = false">Cancel</Button>
          <Button variant="destructive" @click="handleMultiDeleteConfirmed">Delete</Button>
        </div>
      </div>
    </div>
  </div>
</template>
