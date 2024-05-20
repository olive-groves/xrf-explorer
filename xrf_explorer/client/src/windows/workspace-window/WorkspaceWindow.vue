<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Window } from "@/components/ui/window";
import { appState } from "@/lib/app_state";
import { computed } from "vue";

const workspace = computed(() => appState.workspace);
</script>

<template>
  <Window title="Workspace Setup" opened>
    {{ workspace }}
    <Button @click="appState.workspace!.name += '.'">Modify</Button>
  </Window>
</template>
