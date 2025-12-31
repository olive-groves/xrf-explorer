<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ref } from "vue";
import { toast } from "vue-sonner";
import axios from "axios";
import { isErrorWithMessage } from "./duplicates.ts";

// Define emits
const emit = defineEmits<{
  // Close the dialog
  (e: "deleted"): void;
  // Delete specific user and pass (original) username
  (e: "cancel"): void;
}>();

const props = defineProps<{
  /** The currently selected user. */
  user: { original_username: string };
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
      username: user.value.original_username,
    });

    if (response.data.success) {
      toast.info("User deleted successfully");
      emit("deleted");
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
</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Delete Account </DialogTitle>
    <div class="flex items-center justify-between">
      <div class="text-muted-foreground">
        Are you sure you want to delete the following account: <b>{{ user.original_username }}</b> ?
      </div>
    </div>
    <div class="flex items-center justify-end">
      <Button @click="emit('cancel')" class="mr-2"> Cancel </Button>
      <Button @click="deleteUser" variant="destructive"> Delete Account </Button>
    </div>
  </DialogContent>
</template>
