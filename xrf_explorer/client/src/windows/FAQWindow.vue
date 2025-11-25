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
    question: "How do I load a project?",
    answer: "Hover over file menu and click 'New project' or load an already existing project.",
    videoUrl: "https://www.youtube.com/embed/example1",
  },
  {
    question: "How do I reset the client?",
    answer: "Hover over 'XRF-Explorer' and click 'Reset client'. This will clear all local data.",
  },
  {
    question: "How do I switch between light and dark mode?",
    answer: "Hover over 'XRF-Explorer' and select which mode you want to use.",
  },
  {
    question: "Add in FAQs here",
    answer: "Answers here",
  },
  {
    question: "Add in FAQs here",
    answer: "Answers here",
  },
  {
    question: "Add in FAQs here",
    answer: "Answers here",
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
