<script setup lang="ts">
import { Button } from "@/components/ui/button";
import FileInput from "./ui/file-input/FileInput.vue";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
</script>

<template>
  <div class="modal" @click="$emit('close-upload-modal')">
    <Card class="w-8/12 mx-auto mt-20 bg-neutral-700">
      <CardHeader class="text-center text-2xl">Upload files</CardHeader>
      <CardContent class="px-32"> <FileInput /> </CardContent>
      <CardFooter class="flex justify-center">
        <Button>Upload</Button>
      </CardFooter>
    </Card>
  </div>
  div class="modal" @click="$emit('close-upload-modal')"
</template>

<style scoped>
.modal {
  position: fixed; /* Stay in place */
  z-index: 1; /* Sit on top */
  left: 0;
  top: 0;
  width: 100%; /* Full width */
  height: 100%; /* Full height */
  overflow: auto; /* Enable scroll if needed */
  background-color: rgba(0, 0, 0, 0.6); /* Black w/ opacity */
}
</style>
