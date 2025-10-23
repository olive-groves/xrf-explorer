<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { toast } from "vue-sonner";
import { appState } from "@/lib/appState";
import axios from "axios";

// Define emits
const emit = defineEmits(["close"]);



// Interface for API response
interface LogoutResponse {
  success: boolean;
}

// On logout, notify the user, reset stored user role and emit close event
// Function to attempt logout
async function attemptLogout() {

  try {
    const response = await axios.post<LogoutResponse>('/api/logout', {});
    if (response.data.success) {
      
      toast.info(`Logged out successfully`);
      appState.user.username = '';
      appState.user.role = '';
      emit("close");

    }
  }


  catch (error: any) {
    toast.error(error.response?.data?.message || `Logout failed`);
    

  }

}

</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Log out </DialogTitle>
    <div class="flex items-center justify-between">
        <div class="text-muted-foreground">Are you sure you want to log out?</div>
        <Button @click="attemptLogout" >
            Log out
        </Button>
    </div>
  </DialogContent>
</template>