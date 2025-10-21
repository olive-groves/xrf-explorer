<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
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

// Interface for API response
interface LoginResponse {
  success: boolean;
  message: string;
  role: string;
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
    });

    // On success, notify user, set user role, reset fields, and emit close; else give error message
    if (response.data.success) {
      toast.info("Login successful");
      appState.userRole = response.data.role; // Set the user role from the response
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
    <Input placeholder="Username" v-model:model-value="username" />
    <Input placeholder="Password" type="password" v-model:model-value="password" />
    <div class="flex items-center justify-between">
      <Button @click="attemptLogin" :disabled="(username == '') || (password == '')" >
        Log in
      </Button>
    </div>
  </DialogContent>
</template>