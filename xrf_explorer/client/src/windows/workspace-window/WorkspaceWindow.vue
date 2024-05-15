<script setup lang="ts">
import { Window } from "@/components/ui/window";
import { appState } from "@/lib/app_state";
import { computed } from "vue";

const workspace = computed(() => appState.workspace);
</script>

<template>
  <Window title="Workspace Setup">
    {{ workspace }}
  </Window>
</template>
