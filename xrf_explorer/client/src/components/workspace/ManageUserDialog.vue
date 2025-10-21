<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Eye, EyeOff } from "lucide-vue-next";
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

const passwordType = ref("password");

function toggleText() {
  passwordType.value = passwordType.value === "password" ? "text" : "password";
}

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

function validPassword(password: string): boolean {
    if (password === "") {
        return true; // Allow empty password (no change)
    }
    // Password must be between 12 and 32 characters
    const lengthValid = password.length >= 12 && password.length <= 32;

    // Passwords include at least one numeric character [0, 9]
    const numberValid = /[0-9]/.test(password);

    // Password must include at least one special character [!@#$%^&*]
    const specialCharValid = /[!@#$%^&*]/.test(password);

    return lengthValid && numberValid && specialCharValid;
}


</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Update Account </DialogTitle>
    <!-- Input fields -->
    <div class="text">Username</div>
    <Input placeholder="Username" v-model:model-value="username" />
    <div class="text">Password (leave empty to keep current password)</div>
    <div class="flex items-center">
    <Input placeholder="New Password" :type="passwordType" v-model:model-value="password" />
      <Button
        @click="toggleText"
        variant="ghost"
        class="size-8 p-2"
        title="Toggle visibility"
      >
        <Eye v-if="passwordType === 'password'" />
        <EyeOff v-else />
      </Button>
    </div>
    <div v-if="!(password.length >= 12 && password.length <= 32)"class="text-muted-foreground">*Password must be between 12 and 32 characters</div>
    <div v-if="!/[0-9]/.test(password)" class="text-muted-foreground">*Password must include at least one number (0-9)</div>
    <div v-if="!/[!@#$%^&*]/.test(password)" class="text-muted-foreground">*Password must include at least one special character (!@#$%^&*)</div>
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
      <Button @click="updateAccount" :disabled="(username == '') || (role == '') || !validPassword(password)" >
        Update Account
      </Button>
      <Button @click="deleteAccount" variant="destructive">
        Delete Account
      </Button>
    </div>
  </DialogContent>
</template>