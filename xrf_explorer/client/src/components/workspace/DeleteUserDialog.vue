<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ref } from "vue";
import { toast } from "vue-sonner";
import axios from "axios";

// Define emits
const emit = defineEmits(["close"]);
const props = defineProps<{
  /** The currently selected user. */
  user: string;
}>();

// Define user to delete
const user = ref(props.user);

// Interface for API response
interface DeleteUserResponse {
  success: boolean;
  message: string;
  // token: string;
}

/**
 * On deletion, notify the user and emit close event.
 */
async function deleteUser() {
  // Make API call to delete user
  try {
    const response = await axios.post<DeleteUserResponse>("/api/delete_account", {
      username: user.value,
    });

    if (response.data.success) {
      toast.info("User deleted successfully");
      emit("close");
    } else {
      toast.error(response.data.message || "Failed to delete user");
    }
  } catch (error: unknown) {
    if (isErrorWithMessage(error)) {
      toast.error(error.response?.data?.message || "Failed to delete user");
    } else {
      toast.error("Failed to delete user");
    }
  }
}

/**
 * Check if there is an error with the message.
 * @param error The error being checked.
 * @returns Return wether the message gives an error or not.
 */
function isErrorWithMessage(error: unknown): error is { response?: { data?: { message?: string } } } {
  return typeof error === "object" && error !== null && "response" in error;
}
</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Log out </DialogTitle>
    <div class="flex items-center justify-between">
      <div class="text-muted-foreground">
        Are you sure you want to delete the following account: <b>{{ user }}</b> ?
      </div>
    </div>
    <div class="flex items-center justify-end">
      <Button @click="emit('close')" class="mr-2"> Cancel </Button>
      <Button @click="deleteUser" variant="destructive"> Delete </Button>
    </div>
  </DialogContent>
</template>
