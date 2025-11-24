<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ref} from "vue";
import { toast } from "vue-sonner";
import axios from "axios";

// Define emits
const emit = defineEmits(["close"]);
const props = defineProps<{
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

// On deletion, notify the user and emit close event
async function deleteUser() {
  // Make API call to delete user
  try {
    const response = await axios.post<DeleteUserResponse>('/api/delete_account', {
      username: user.value
    });

    if (response.data.success) {
      toast.info("User deleted successfully");
      emit("close");
    } else {
      toast.error(response.data.message || "Failed to delete user");
    }
  } catch (error: any) {
    toast.error(error.response?.data?.message || "Failed to delete user");
  }
}

</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Log out </DialogTitle>
    <div class="flex items-center justify-between">
        <div class="text-muted-foreground">Are you sure you want to delete the following account: <b>{{ user }}</b> ?</div>
        <Button @click="deleteUser" variant="destructive" >
            Delete
        </Button>
    </div>
  </DialogContent>
</template>