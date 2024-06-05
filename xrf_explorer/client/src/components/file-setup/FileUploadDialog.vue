<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Dialog, DialogTrigger, DialogContent, DialogTitle } from "@/components/ui/dialog";

const emit = defineEmits(["filesUploaded"]);
</script>

<template>
  <Dialog>
    <DialogTrigger>
      <Button variant="outline">Upload files</Button>
    </DialogTrigger>
    <DialogContent>
      <DialogTitle class="text-sm font-bold">Upload files</DialogTitle>
      <Button @click="emit('filesUploaded')"></Button>
    </DialogContent>
  </Dialog>
</template>
