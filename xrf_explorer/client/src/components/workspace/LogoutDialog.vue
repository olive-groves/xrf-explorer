<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { appState } from "@/lib/appState";
import { toast } from "vue-sonner";

// Define emits
const emit = defineEmits(["close"]);

// On logout, notify the user, reset stored user role and emit close event
function logout() {
    toast.info(`Logged out successfully`);
    appState.user.username = '';
    appState.user.role = '';
    // appState.token = '';
    emit("close");

}

</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Log out </DialogTitle>
    <div class="flex items-center justify-between">
        <div class="text-muted-foreground">Are you sure you want to log out?</div>
        <Button @click="logout" >
            Log out
        </Button>
    </div>
  </DialogContent>
</template>