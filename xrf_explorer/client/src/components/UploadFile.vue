<script setup lang="ts">

import {Button} from "@/components/ui/button";
</script>

<template>
  <head>
    <Title>Upload a File here!</Title>
  </head>
  <body>
    <form method="POST" enctype="multipart/form-data">
      {{ form.hidden_tag() }}
      {{ form.file() }}
      {{ form.submit() }}
    </form>
    <button type="button" class="btn btn-success">Upload</button>
  </body>
</template>

<style scoped>

</style>