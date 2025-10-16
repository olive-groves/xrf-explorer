<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ref} from "vue";
import { toast } from "vue-sonner";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import axios from "axios";

const emit = defineEmits(["close"]);

const username = ref("");
const password = ref("");
const role = ref("");

interface CreateAccountResponse {
  success: boolean;
  message?: string;
}

async function createAccount() {
  if (!username.value || !password.value || !role.value) {
    toast.error("All fields are required");
    return;
  }

  try {
    const response = await axios.post<CreateAccountResponse>('/api/create_account', {
      username: username.value,
      password: password.value,
      role: role.value.toUpperCase()  // Ensure role is uppercase to match backend enum
    });

    if (response.data.success) {
      toast.info("Account created successfully");
      resetFields();
      emit("close");
    } else {
      toast.error(response.data.message || "Account creation failed");
    }
  } catch (error: any) {
    toast.error("Account creation failed");
  }
}

function resetFields() {
    username.value = "";
    password.value = "";
    role.value = "";
}
defineExpose({ resetFields });


</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Create Account </DialogTitle>
    <Input placeholder="Username" v-model:model-value="username" />
    <Input placeholder="Password" v-model:model-value="password" />
    <Select v-model="role" class="w-full mb-4">
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
      <Button @click="createAccount" :disabled="(username == '') || (password == '') || (role == '')" >
        Create Account
      </Button>
    </div>
  </DialogContent>
</template>