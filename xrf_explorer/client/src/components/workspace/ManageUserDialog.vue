<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ref} from "vue";
import { toast } from "vue-sonner";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import axios from "axios";

// Define emits
const emit = defineEmits<{
    (e: 'close'): void, // Close the dialog
    (e: 'deleteAccount', deleteUser: {original_username: string}): void // Delete specific user and pass (original) username
}>();

const props = defineProps<{
    user: {original_username: string; username: string; role: string} // User data passed from parent
}>();

const originalUsername = ref(props.user.original_username);  // Store original username to identify the account to update
const username = ref(props.user.username); // Selected username
const password = ref(""); // New password (optional)
const role = ref(props.user.role.toLowerCase()); // Selected role

// Interface for API response
interface UpdateAccountResponse {
  success: boolean;
  message?: string;
}

// Function to update account
async function updateAccount() {
  // Check if at least username and role are filled
  if (!username.value || !role.value) {
    toast.error("Username and Role are required");
    return;
  }

  // Make API call to update account
  try {
    const response = await axios.post<UpdateAccountResponse>('/api/update_account', {
      originalUsername: originalUsername.value,
      username: username.value,
      password: password.value,
      role: role.value.toUpperCase()  // Ensure role is uppercase to match backend enum
    });

    // On success, notify user and emit close; else give error message
    if (response.data.success) {
      toast.info("Account updated successfully");
      emit("close");
    } else {
      toast.error(response.data.message || "Account update failed");
    }
  } catch (error: any) {
    toast.error("Account update failed");
  }
}

function deleteAccount() {
    emit("deleteAccount", {original_username: originalUsername.value});
}


</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Update Account </DialogTitle>
    <!-- Input fields -->
    <Input placeholder="Username" v-model:model-value="username" />
    <Input placeholder="New Password" v-model:model-value="password" />
    <Select v-model="role" class="w-full mb-4">
        <!-- Dropdown for role select -->
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Roles</SelectLabel>
              <SelectItem value="admin">Admin</SelectItem>
              <SelectItem value="editor">Editor</SelectItem>
              <SelectItem value="viewer">Viewer</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
    <div class="flex items-center justify-between">
      <Button @click="emit('close')" >
        Cancel
      </Button>
      <Button @click="updateAccount" :disabled="(username == '') || (role == '')" >
        Update Account
      </Button>
      <Button @click="deleteAccount">
        Delete Account
      </Button>
    </div>
  </DialogContent>
</template>