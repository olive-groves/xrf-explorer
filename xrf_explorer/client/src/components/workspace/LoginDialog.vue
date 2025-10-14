<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ref} from "vue";
import { appState } from "@/lib/appState";
import { toast } from "vue-sonner";

const emit = defineEmits(["close"]);

const username = ref("");
const password = ref("");

const storedAccounts = ref([
  { username: "admin", password: "admin", role: "admin" },
  { username: "editor", password: "pass", role: "editor" },
  { username: "viewer", password: "password", role: "viewer" }
]);

function attemptLogin() {
    const account = storedAccounts.value.find(acc => acc.username === username.value && acc.password === password.value);
    if (account) {
        toast.info("Login successful");
        appState.userRole = account.role;
        username.value = "";
        password.value = "";
        emit("close");
    } else {
      toast.error("Invalid username or password");
    }
}

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
    <Input placeholder="Password" v-model:model-value="password" />
    <div class="flex items-center justify-between">
      <Button @click="attemptLogin" :disabled="(username == '') || (password == '')" >
        Log in
      </Button>
    </div>
  </DialogContent>
</template>