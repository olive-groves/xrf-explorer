<script setup lang="ts">
import { Window } from '@/components/ui/window';
// import { ref } from 'vue';
import { Button } from '@/components/ui/button';

function getEmbedding() {
  return 'http://localhost:8001/api/get_overlay';
}

</script>

<template>
  <Window title="Dimensionality reduction">
    <img :src="getEmbedding()" />
    <Button>Generate embedding</Button>
  </Window>
</template>