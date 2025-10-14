<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ref} from "vue";
import { toast } from "vue-sonner";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";

const emit = defineEmits(["close"]);

const username = ref("");
const password = ref("");
const role = ref("");

const storedAccounts = ref([
  { username: "admin", password: "", role: "admin" },
  { username: "editor", password: "", role: "editor" },
  { username: "viewer", password: "", role: "viewer" },
]);

function createAccount() {
  // Check for duplicate accountname
  const exists = storedAccounts.value.some(acc => acc.username === username.value);
  if (exists) {
    toast.error(`Account for '${username.value}' already exists.`);
    return;
  }
  storedAccounts.value.push({ username: username.value, password: password.value, role: role.value });
  console.log("Stored Accounts:", storedAccounts.value);
  toast.info(`Account for '${storedAccounts.value[storedAccounts.value.length - 1].username}' created successfully`);
  emit("close");
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