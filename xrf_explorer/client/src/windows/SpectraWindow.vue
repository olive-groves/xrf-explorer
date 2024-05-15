<script setup lang="ts">
import { Window } from "@/components/ui/window";
import { ref } from "vue";
import { Button } from "@/components/ui/button";

const count = ref(0);
</script>

<template>
    <div>
      <Window title="Test window" opened>
        <Button @click="count++">{{ count }}</Button
        ><br />
        <br />
      </Window>
      <Window title="Second window"> Hello there </Window>
      <Window title="Button window" no-scroll>
      </Window>
    </div>
  </template>