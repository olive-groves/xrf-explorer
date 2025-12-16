<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { toast } from "vue-sonner";
import { appState } from "@/lib/appState";
import axios from "axios";
import { isErrorWithMessage } from "./duplicates.ts";

// Define emits
const emit = defineEmits(["close"]);

// Interface for API response
interface LogoutResponse {
  success: boolean;
}

/**
 * Attempt to log out the user. On logout, notify the user, reset stored user data and emit close event.
 */
async function attemptLogout() {
  try {
    const response = await axios.post<LogoutResponse>("/api/logout", {});
    if (response.data.success) {
      toast.info(`Logged out successfully`);
      appState.user.username = "";
      appState.user.role = "";
      appState.user.projects = [];
      location.reload(); // To unload the current data. Sorry for any future developers.
      emit("close");
    }
  } catch (error: unknown) {
    if (isErrorWithMessage(error)) {
      toast.error(error.response?.data?.message || "Logout failed");
    } else {
      toast.error("Logout failed");
    }
  }
}
</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Log out </DialogTitle>
    <div class="flex items-center justify-between">
      <div class="text-muted-foreground">Are you sure you want to log out?</div>
      <Button @click="attemptLogout"> Log out </Button>
    </div>
  </DialogContent>
</template>
