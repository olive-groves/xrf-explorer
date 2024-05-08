<script setup lang="ts">
import { reactive } from 'vue'

// Constants
const API_URL = 'http://localhost:8001/api'

// Reactive array
var file_names: string[] = reactive([]);

// Fetch data from the server
async function fetchdata() {
  try {
    // Try fethcing data from the server
    const response = await fetch(`${API_URL}/files`, {
    method:"GET",
    headers: {
      "Content-Type":"application/json"
    }
  });

  // Convert the response to JSON
  const data = await response.json() as Array<string>;

  // Add files to the list 
  data.forEach((file) => {
    file_names.push(file);
  });

  } catch (error) {
    console.log("Fetching files gave error: ", error);
  }
}

fetchdata()

</script>

<template>
  <ul>
    <li v-for="file in file_names">
      {{ file }}
    </li>
  </ul>
</template>

<style scoped>
</style>
