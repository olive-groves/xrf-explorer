<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Eye, EyeOff } from "lucide-vue-next";
import { Input } from "@/components/ui/input";
import { ref } from "vue";
import { toast } from "vue-sonner";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import axios from "axios";

// Define emits
const emit = defineEmits(["close"]);

// Define User Input Fields
const username = ref("");
const password = ref("");
const role = ref("");

const passwordType = ref("password");

/**
 * Toggle the password mode between password and text.
 */
function toggleText() {
  passwordType.value = passwordType.value === "password" ? "text" : "password";
}

// Interface for API response
interface CreateAccountResponse {
  success: boolean;
  message?: string;
}

/**
 * Create an account.
 */
async function createAccount() {
  // Check if all fields are filled
  if (!username.value || !password.value || !role.value) {
    toast.error("All fields are required");
    return;
  }

  if (!validPassword(password.value)) {
    toast.error("Password does not meet requirements");
    return;
  }

  // Make API call to create account
  try {
    const response = await axios.post<CreateAccountResponse>("/api/create_account", {
      username: username.value,
      password: password.value,
      role: role.value.toUpperCase(), // Ensure role is uppercase to match backend enum
    });

    // On success, notify user and reset fields, else give error message
    if (response.data.success) {
      toast.info("Account created successfully");
      resetFields();
      emit("close");
    } else {
      toast.error(response.data.message || "Account creation failed");
    }
  } catch (error: unknown) {
    toast.error("Account creation failed");
  }
}

/**
 * Reset the input fields.
 */
function resetFields() {
  username.value = "";
  password.value = "";
  role.value = "";
}
defineExpose({ resetFields });

/**
 * Check if the user entered a valid password.
 * @param password The password entered by the user.
 * @returns Returns whether the password is valid or not.
 */
function validPassword(password: string): boolean {
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
    <DialogTitle class="mb-2 font-bold"> Create Account </DialogTitle>
    <!-- Input fields for Username and Password -->
    <div class="text-base">Username</div>
    <Input placeholder="Username" v-model:model-value="username" />
    <div class="text-base">Password</div>
    <div class="flex items-center">
      <Input @keydown.space.prevent placeholder="Password" :type="passwordType" v-model:model-value="password" />
      <Button @click="toggleText" variant="ghost" class="size-8 p-2" title="Toggle visibility">
        <Eye v-if="passwordType === 'password'" />
        <EyeOff v-else />
      </Button>
    </div>
    <div v-if="!(password.length >= 12 && password.length <= 32)" class="text-muted-foreground">
      *Password must be between 12 and 32 characters
    </div>
    <div v-if="!/[0-9]/.test(password)" class="text-muted-foreground">
      *Password must include at least one number (0-9)
    </div>
    <div v-if="!/[!@#$%^&*]/.test(password)" class="text-muted-foreground">
      *Password must include at least one special character (!@#$%^&*)
    </div>
    <Select v-model="role" class="mb-4 w-full">
      <!-- Dropdown menu to select role from Admin, Editor, and Viewer-->
      <SelectTrigger>
        <SelectValue placeholder="Select a user role" />
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
      <Button @click="createAccount" :disabled="username == '' || !validPassword(password) || role == ''">
        Create Account
      </Button>
    </div>
  </DialogContent>
</template>
