<script setup lang="ts">
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { AdditionalSettingsDialog, FileSetupTable } from ".";
import { WorkspaceConfig } from "@/lib/workspace";
import { validateWorkspace } from "./utils";
import { computed } from "vue";
import { resetWindow } from "@/lib/utils";
import { TriangleAlert } from "lucide-vue-next";
</script>

<template>
  <DialogContent class="max-w-fit">
    <div class="w-[22rem] space-y-4">
      <!-- Header -->
      <DialogTitle class="mb-2 font-bold"> Are you sure you want to reset the client? </DialogTitle>
      <!-- Text and button -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-1.5">
          <TriangleAlert class="size-5 text-primary" />
          <div class="text-muted-foreground">This will refresh the webpage</div>
        </div>
        <Button @click="resetWindow">Confirm</Button>
      </div>
    </div>
  </DialogContent>
</template>
