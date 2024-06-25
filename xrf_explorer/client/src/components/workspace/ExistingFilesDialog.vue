<script setup lang="ts">
import { DialogContent, DialogTitle, DialogClose } from "@/components/ui/dialog";
import { FrontendConfig } from "@/lib/config";
import { useFetch } from "@vueuse/core";
import { computed, inject, ref, toRef } from "vue";

const config = inject<FrontendConfig>("config")!;

const props = defineProps<{
  /**
   * The name of the relevant project.
   */
  name: string;
}>();

const emit = defineEmits(["deleted"]);

const name = toRef(props, "name");
const files = ref();

async function getFiles() {
  const fileUrl = computed(() => `${config.api.endpoint}/${name.value}/files`);
  const fileFetch = useFetch<string>(fileUrl, { refetch: true });
  files.value = computed<string[]>(() => JSON.parse(fileFetch.data.value ?? "[]"));
}

/**
 * Deletes all files and recreates the project directory.
 */
async function deleteFiles() {
  await fetch(`${config.api.endpoint}/${name.value}/delete`, { method: "DELETE" });
  await fetch(`${config.api.endpoint}/${name.value}/create`, { method: "POST" });
  emit("deleted");
}
</script>

<template>
  <DialogContent v-model:open="getFiles">
    <DialogTitle class="font-bold">Existing files</DialogTitle>
    <div>There are preexisting files for project {{ name }}.</div>
    <div>
      <div v-for="file in files" :key="file" v-text="file" class="text-xs text-muted-foreground" />
    </div>
    <div class="flex w-full justify-end space-x-2">
      <Button variant="destructive" @click="deleteFiles">Delete files</Button>
      <DialogClose>
        <Button>Keep files</Button>
      </DialogClose>
    </div>
  </DialogContent>
</template>
