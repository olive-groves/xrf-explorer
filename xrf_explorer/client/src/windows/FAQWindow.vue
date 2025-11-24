<script setup lang="ts">
import { ref } from "vue";
import { faqWindowOpen } from "@/lib/windowState";

interface FAQItem {
  question: string;
  answer: string;
  videoUrl?: string;
}

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

const closeFAQ = () => {
  faqWindowOpen.value = false;
};
</script>

<template>
  <div class="w-full h-full p-6 overflow-auto bg-background">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">FAQ</h1>
      <button
        @click="closeFAQ"
        class="px-2 py-1 rounded bg-accent text-accent-foreground hover:opacity-80"
      >
        ✕
      </button>
    </div>

    <div v-for="(item, i) in faqItems" :key="i" class="mb-6 border rounded-md p-4 shadow-sm">
      <details>
        <summary class="font-semibold text-lg cursor-pointer">{{ item.question }}</summary>
        <p class="mt-2">{{ item.answer }}</p>
        <iframe
          v-if="item.videoUrl"
          :src="item.videoUrl"
          class="w-full h-64 mt-2"
          frameborder="0"
          allowfullscreen
        />
      </details>
    </div>
  </div>
</template>