<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogScrollContent, DialogTitle } from "@/components/ui/dialog";
import { WorkspaceConfig } from "@/lib/workspace";
import { validateWorkspace } from "./utils";
import { computed } from "vue";
import { TriangleAlert } from "lucide-vue-next";
import { ScrollArea } from "@/components/ui/scroll-area";

const model = defineModel<WorkspaceConfig>({ required: true });

const emit = defineEmits(["save"]);

const modelValid = computed(() => validateWorkspace(model.value));

/**
 * Emit the save event, prompting the containing element to save the updated setup.
 */
function save() {
  emit("save");
}
</script>

<template>
  <DialogScrollContent>
    <div class="space-y-4">
      <!-- Header -->
      <DialogTitle class="font-bold">Set up elemental channels</DialogTitle>

      <!-- Content -->
      <ScrollArea class="h-72">
        <div class="grid grid-cols-[min-content,min-content,1fr] grid-rows-[repeat(2.25rem)] gap-2">
          <template v-for="channel in model.elementalChannels" :key="channel.channel">
            <div class="flex justify-end text-muted-foreground">
              <div v-text="channel.channel" class="h-min self-center" />
            </div>
            <Checkbox v-model:checked="channel.enabled" class="my-2.5 size-4" />
            <Input v-model="channel.name" />
          </template>
        </div>
      </ScrollArea>

      <!-- Footer -->
      <div class="flex justify-between">
        <div class="flex items-end space-x-1.5">
          <TriangleAlert v-if="!modelValid[0]" class="size-5 text-primary" />
          <div class="text-muted-foreground" v-text="modelValid[1]" />
        </div>
        <div class="space-x-2">
          <Button :disabled="!modelValid[0]" @click="save">Save</Button>
        </div>
      </div>
    </div>
  </DialogScrollContent>
</template>
