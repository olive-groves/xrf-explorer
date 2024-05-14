<script setup lang="ts">
import { Header } from "@/components";
import { WindowContainer } from "@/components/ui/window";
import { ImageViewer } from "@/components/image-viewer";

// Import all windows
import { TestWindow } from "@/windows";

// Import all reusable dialogs
import { UploadFileDialog } from "@/components/dialogs";
</script>

<template>
  <div class="grid h-screen w-screen grid-cols-1 grid-rows-[min-content_1fr]">
    <Header />
    <WindowContainer>
      <ImageViewer />

      <!-- Place all windows below here -->
      <TestWindow />
    </WindowContainer>

    <!-- Place all reusable dialogs here -->
    <UploadFileDialog />
  </div>
</template>
