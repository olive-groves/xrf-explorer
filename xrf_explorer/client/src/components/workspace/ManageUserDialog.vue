<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ref} from "vue";
import { toast } from "vue-sonner";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import axios from "axios";

const emit = defineEmits(["close"]);
const props = defineProps<{
    user: {original_username: string; username: string; role: string}
}>();

const originalUsername = ref(props.user.original_username);  // Store original username to identify the account to update
const username = ref(props.user.username);
const password = ref("");
const role = ref(props.user.role.toLowerCase());

interface UpdateAccountResponse {
  success: boolean;
  message?: string;
}

async function updateAccount() {
  if (!username.value || !role.value) {
    toast.error("Username and Role are required");
    return;
  }

  try {
    const response = await axios.post<UpdateAccountResponse>('/api/update_account', {
      originalUsername: originalUsername.value,
      username: username.value,
      password: password.value,
      role: role.value.toUpperCase()  // Ensure role is uppercase to match backend enum
    });

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


</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Update Account </DialogTitle>
    <Input placeholder="Username" v-model:model-value="username" />
    <Input placeholder="New Password" v-model:model-value="password" />
    <Select v-model="role" class="w-full mb-4">
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
      <Button>
        Delete Account
      </Button>
    </div>
  </DialogContent>
</template>