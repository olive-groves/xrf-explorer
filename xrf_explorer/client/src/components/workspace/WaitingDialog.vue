<script setup lang="ts">
import { Label } from "@/components/ui/label";
import { VisuallyHidden } from "radix-vue";
import { AlertDialogContent, AlertDialogTitle } from "../ui/alert-dialog";

const emit = defineEmits(["save"]);

</script>
<template>
    <AlertDialogContent>
        <VisuallyHidden>
            <AlertDialogTitle></AlertDialogTitle>
        </VisuallyHidden>
        <div class="text-center">
            <Label>Initializing workspace. This can take a few minutes.</Label>
        </div>
    </AlertDialogContent>
</template>