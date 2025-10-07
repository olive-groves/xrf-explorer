<script setup lang="ts">
import { Button } from '@/components/ui/button';

const emit = defineEmits(["close"]);

function onPreview() {

}

function onExit() {
  emit("close"); // close the window
}

</script>

<template>
  <Window title="Stitch" location="right">

  </Window>
</template>