<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Eye, EyeOff } from "lucide-vue-next";
import { Input } from "@/components/ui/input";
import { ref} from "vue";
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

function toggleText() {
  passwordType.value = passwordType.value === "password" ? "text" : "password";
}

// Interface for API response
interface LoginResponse {
  success: boolean;
  message: string;
  username: string;
  role: string;
  // token: string;
}

// Function to attempt login
async function attemptLogin() {
  if (!username.value || !password.value) {
    toast.error("Invalid username or password");
    return;
  }

  // Make API call to login
  try {
    const response = await axios.post<LoginResponse>('/api/login', {
      username: username.value,
      password: password.value
      // token: token.value
    });

    // On success, notify user, set user role, reset fields, and emit close; else give error message
    if (response.data.success) {
      toast.info("Login successful");
      appState.user.username = response.data.username; // Set the username in appState
      appState.user.role = response.data.role; // Set the user role from the response
      // appState.token = response.data.token; // Set the auth token from the response
      resetFields();
      emit("close");
    } else {
      toast.error("Invalid username or password");
    }
  } catch (error: any) {
    toast.error(error.response?.data?.message || "Login failed" );
  }
}

// Function to reset input fields
function resetFields() {
  username.value = "";
  password.value = "";
}
defineExpose({ resetFields });

</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Log in </DialogTitle>
    <div class="text">Username</div>
    <Input placeholder="Username" v-model:model-value="username" />
    <div class="text">Password</div>
    <div class="flex items-center">
    <Input placeholder="Password" :type="passwordType" v-model:model-value="password" />
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
    <div class="flex items-center justify-between">
      <Button @click="attemptLogin" :disabled="(username == '') || (password == '')" >
        Log in
      </Button>
    </div>
  </DialogContent>
</template>