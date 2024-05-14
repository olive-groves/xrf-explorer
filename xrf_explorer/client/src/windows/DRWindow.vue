<script setup lang="ts">
import { ref } from 'vue';
import { useFetch, useImage } from '@vueuse/core'

import { Window } from '@/components/ui/window';
import { Button } from '@/components/ui/button';

function getDRImage() {
  return 'http://localhost:8001/api/get_overlay';
}

var threshold = ref(100)
var selectedElement = ref(9)

const { isLoading } = useImage({ src: getDRImage() })
const isError = ref(false)

async function updateEmbedding() {
  const _url = new URL('http://localhost:8001/api/get_embedding');
  // _url.searchParams.set('element', selectedElement.value.toString());
  _url.searchParams.set('threshold', threshold.value.toString());

  const { isFetching, error, data } = await useFetch(_url.toString(), { method: 'GET' });
  console.log("isFetching: ", isFetching)
  console.log("error: ", error)
  console.log("data", data)
}

</script>

<template>
  <Window title="Dimensionality reduction">
    <span v-if="isLoading">Loading...</span>
    <span v-if="isError">Error!</span>
    <img v-else :src="getDRImage()" @error="isError = true">

    <!-- <img :src="getEmbedding()" /> -->
    <p>Threshold: {{ threshold }}</p>
    <input type="range" v-model="threshold" min=0 max=100>
    <br>
    <p>Element: {{ selectedElement }}</p>
    <select v-model="selectedElement">
      <option value="0">Element 0</option>
      <option value="1">Element 1</option>
      <option value="9">Element 9</option>
    </select>
    <Button @click="updateEmbedding">Generate</Button>
  </Window>
</template>