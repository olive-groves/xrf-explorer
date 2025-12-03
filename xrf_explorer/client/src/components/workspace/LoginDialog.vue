<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Eye, EyeOff } from "lucide-vue-next";
import { Input } from "@/components/ui/input";
import { ref } from "vue";
import { appState } from "@/lib/appState";
import { toast } from "vue-sonner";
import axios from "axios";

// Define emits
const emit = defineEmits(["close"]);

// Define User data
const username = ref("");
const password = ref("");
// const token = ref("");

const passwordType = ref("password");

/**
 * Toggle password visibility.
 */
function toggleText() {
  passwordType.value = passwordType.value === "password" ? "text" : "password";
}

// Interface for API response
interface LoginResponse {
  success: boolean;
  message: string;
  username: string;
  role: string;
  projects: string[];
  // token: string;
}

/**
 * Attempt to log in the user.
 */
async function attemptLogin() {
  if (!username.value || !password.value) {
    toast.error("Invalid username or password");
    return;
  }

  // Make API call to login
  try {
    const response = await axios.post<LoginResponse>("/api/login", {
      username: username.value,
      password: password.value,
    });

    // On success, notify user, set user role, reset fields, and emit close; else give error message
    if (response.data.success) {
      toast.info("Login successful");
      appState.user.username = response.data.username; // Set the username in appState
      appState.user.role = response.data.role; // Set the user role from the response
      appState.user.projects = response.data.projects; // Set the user projects from the response
      resetFields();
      emit("close");
    } else {
      toast.error("Invalid username or password");
    }
  } catch (error: unknown) {
    if (isErrorWithMessage(error)) {
      toast.error(error.response?.data?.message || "Login failed");
    } else {
      toast.error("Login failed");
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

/**
 * Reset the input fields.
 */
function resetFields() {
  username.value = "";
  password.value = "";
}
defineExpose({ resetFields });
</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Log in </DialogTitle>
    <div class="text-base">Username</div>
    <Input placeholder="Username" v-model:model-value="username" />
    <div class="text-base">Password</div>
    <div class="flex items-center">
      <Input placeholder="Password" :type="passwordType" v-model:model-value="password" @keyup.enter="attemptLogin" />
      <Button @click="toggleText" variant="ghost" class="size-8 p-2" title="Toggle visibility">
        <Eye v-if="passwordType === 'password'" />
        <EyeOff v-else />
      </Button>
    </div>
    <div class="flex items-center justify-between">
      <Button @click="attemptLogin" :disabled="username == '' || password == ''"> Log in </Button>
    </div>
  </DialogContent>
</template>
