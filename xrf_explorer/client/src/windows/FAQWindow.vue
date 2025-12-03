<script setup lang="ts">
import { ref } from "vue";
import { faqWindowOpen } from "@/lib/windowState";

interface FAQItem {
  question: string;
  answer: string;
  videoUrl?: string;
}

/**
 * The items to be display in the FAQ. Format: question: "", answer: "", videoUrl:"".
 */
const faqItems = ref<FAQItem[]>([
  {
    question: "What is XRF-Explorer? and how do I use it?",
    answer: "XRF-Explorer is a tool to help you explore XRF data files. You can load your data files into a project and visualize them using various built-in tools.",
  },
  {
    question: "Where can you find more information about XRF-Explorer?",
    answer: "Press the XRF-Explorer button in the top left corner and click on 'Github' or 'Code documentation' or 'Technical documents' to find more information about XRF-Explorer. Depending on what you are looking for.",
  },
  {
    question: "How do I load a project?",
    answer: "Hover over 'file' in the menu bar and click 'New project' or load an already existing project. If your assigned role prevents you from loading a project, please contact your administrator.",
    videoUrl: "https://www.youtube.com/watch?v=xvFZjo5PgG0&list=RDxvFZjo5PgG0&start_radio=1",
  },
  {
    question: "Where can I find my imported data files? (Editor & Admin role only)",
    answer: "Click on 'view' in the menu bar and select 'Workspace'. A sidebar will appear on the left side of the window, displaying all data sources.",
  },
  {
    question: "How do I delete a project? (Editor & Admin role only)",
    answer: "Open the 'Workspace' from the 'view' menu, click on 'Delete project' at the bottom of the sidebar, and confirm the deletion.",
  },
  {
    question: "How do I upload data files to a project? (Editor & Admin role only)",
    answer: "In the workspace sidebar, right-click on the gear icon next to the data source, this will open a context menu where you can select 'Upload files'. You can then choose the file you want to upload from your computer.",
  },
  {
    question: "How do I delete workspace data files (server)? (Editor & Admin role only)",
    answer: "In the workspace sidebar, right-click on the gear icon next to the data source, this will open a context menu where you can select 'Delete files'. This will open a dialog where you can select which files to delete from the server. You will be asked to confirm the deletion. Please note that this action is irreversible and will permanently delete the files from the server.",
  },
  {
    question: "How do I delete workspace data files (local)? (Editor & Admin role only)",
    answer: "In the workspace sidebar, right-click on the gear icon next to the data source, this will open a context menu where you can select the red trash bin icon to delete the data source next to it. You will be asked to confirm the deletion. This will only delete the data source from the workspace, not the actual file on your computer.",
  },
  {
    question: "How do I add workspace components? (Editor & Admin role only)",
    answer: "In the workspace sidebar, right-click on the gear icon next to the data source, this will open a context menu where you can select 'Add component'. You can then choose from the available components to add to your workspace.",
  },
  {
    question: "How do I reset the client and what does it do?",
    answer: "Hover over 'XRF-Explorer' and click 'Reset client'. This will clear all local data and settings, returning the client to its default state.",
  },
  {
    question: "What permissions does viewer role have?",
    answer: "Viewer role allows you to view projects, but you cannot create, edit, or delete projects or data files. You can only view the data and visualizations that have been shared with you.",
  },
  {
    question: "What permissions does editor role have?",
    answer: "Editor role allows you to create, edit, and delete projects and data files. You can also upload new data files to the server and manage existing ones.",
  },
  {
    question: "What permissions does admin role have?",
    answer: "Admin role has all the permissions of the editor role, plus additional administrative capabilities such as managing user roles and settings.",
  },
  {
    question: "What does the 'Elemental channels' tab do?",
    answer: "Select which elements you want to visualize in the main window. You are able to select their thresholds and colors.",
  },
  {
    question: "What does the 'Dimensionality reduction' tab do?",
    answer: "After selecting an element and overlay, you can choose to apply dimensionality reduction techniques to visualize complex data in a simplified manner.",
  },
  {
    question: "What does the 'Layers' tab do?",
    answer: "In the Layers tab you can manage the different layers of your visualization, such as adding or removing layers, adjusting their opacity, and changing their order.",
  },
  {
    question: "What does the 'Spectrum' tab do?",
    answer: "In the Spectrum tab you can view the spectrum of the selected data point or region, allowing you to analyze the elemental composition in detail.",
  },
  {
    question: "What does the 'Elemental charts' tab do?",
    answer: "In the Elemental charts tab you can see an average abundace chart of all the selected elements within the selected part of the painting or whole painting.",
  },
  {
    question: "What does the 'Color segmentation' tab do?",
    answer: "In the Color Segmentation tab you can apply color segmentation techniques to identify and visualize different color regions within the painting.",
  },
  {
    question: "What is stitching and how does it work?",
    answer: "Stitching is the process of combining multiple data files or images into a single cohesive visualization. This is particularly useful when dealing with large datasets that cannot be captured in a single scan. We use algorithms to align and merge the data based on overlapping regions.",
  },
  {
    question: "How do I switch between light and dark mode?",
    answer: "Hover over 'XRF-Explorer' and select which mode you want to use.",
  },
  {
    question: "Still need help?",
    answer: "If you still need help, please visit our GitHub page or contact your administrator for further assistance.",
  },
]);

/**
 * Set global boolean, default is false.
 */
const closeFAQ = () => {
  faqWindowOpen.value = false;
};
</script>

<template>
  <div class="size-full overflow-auto p-6">
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold">FAQ</h1>
      <button @click="closeFAQ" class="rounded px-2 py-1 hover:opacity-80">✕</button>
    </div>

    <!-- The questions and answers -->
    <div v-for="(item, i) in faqItems" :key="i" class="mb-6 rounded-md border p-4 shadow-sm">
      <details>
        <summary class="cursor-pointer text-lg font-semibold">{{ item.question }}</summary>
        <p class="mt-2">{{ item.answer }}</p>
        <iframe v-if="item.videoUrl" :src="item.videoUrl" class="mt-2 h-64 w-full" frameborder="0" allowfullscreen />
      </details>
    </div>
  </div>
</template>
