<script setup lang="ts">
import { Button } from '@/components/ui/button';
import {
  ReusableDialog,
  DialogFooter,
  DialogClose,
  DialogTitle
} from '@/components/ui/dialog';
import { FileInput } from '@/components/ui/file-upload';
</script>

<template>
  <ReusableDialog id="upload_file">
    <DialogTitle>
      Upload files
    </DialogTitle>

    <FileInput />
    
    <DialogFooter>
      <DialogClose>
        <Button variant="destructive">
          Cancel
        </Button>
      </DialogClose>
      <Button>Upload</Button>
    </DialogFooter>
  </ReusableDialog>
</template>