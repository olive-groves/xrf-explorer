<script setup lang="ts">
import Button from "./ui/button/Button.vue";
</script>

<template>
  <form action="/upload" method="post" enctype="multipart/form-data">
    <input style="display: block" type="file" name="fileUpload" />
    <Button style="margin-top: 10px">
      <input type="submit" value="Upload file" />
    </Button>
  </form>
</template>

<style scoped></style>
