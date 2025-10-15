<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ref, computed } from "vue";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
// import { toast } from "vue-sonner";

const emit = defineEmits(["close", "createAccount"]);

const searchQuery = ref("");

const username = ref("");
const password = ref("");
const role = ref("");

const storedAccounts = ref([
  { username: "admin1", password: "admin", role: "admin" },
  { username: "editor1", password: "pass", role: "editor" },
  { username: "viewer1", password: "password", role: "viewer" },
  { username: "admin2", password: "admin", role: "test" },
  { username: "editor2", password: "pass", role: "editor" },
  { username: "viewer2", password: "password", role: "viewer" },
  { username: "admin3", password: "admin", role: "admin" },
  { username: "test3", password: "pass", role: "editor" },
  { username: "viewer3", password: "password", role: "viewer" },
  { username: "admin4", password: "admin", role: "admin" },
  { username: "editor4", password: "pass", role: "editor" },
  { username: "viewer4", password: "password", role: "viewer" },
  { username: "admin5", password: "admin", role: "admin" },
  { username: "editor5", password: "pass", role: "editor" },
  { username: "viewer5", password: "password", role: "viewer" },
  { username: "admin6", password: "admin", role: "admin" },
  { username: "editor6", password: "pass", role: "editor" },
  { username: "viewer6", password: "password", role: "viewer" },
  { username: "admin7", password: "admin", role: "admin" },
  { username: "editor7", password: "pass", role: "editor" },
  { username: "viewer7", password: "password", role: "viewer" },
  { username: "admin8", password: "admin", role: "admin" },
  { username: "editor8", password: "pass", role: "editor" },
  { username: "viewer8", password: "password", role: "viewer" },
  { username: "admin9", password: "admin", role: "admin" },
  { username: "editor9", password: "pass", role: "editor" },
  { username: "viewer9", password: "password", role: "viewer" },
  ]);

function resetFields() {
    username.value = "";
    password.value = "";
    role.value = "";
}
defineExpose({ resetFields });

// Filter logic
const filteredAccounts = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  if (!query) return storedAccounts.value;
  return storedAccounts.value.filter(
    (a) =>
      a.username.toLowerCase().includes(query) ||
      a.role.toLowerCase().includes(query)
  );
});

</script>

<template>
  <DialogContent ref="dialog" class="p-4">
    <DialogTitle class="mb-2 font-bold"> Manage Accounts </DialogTitle>
        <div>
            <Button @click="$emit('createAccount')" >
                Create Account
            </Button>
        </div>
         <!-- 🔍 Search bar -->
        <div>
            <Input
                v-model="searchQuery"
                placeholder="Search by username or role..."
            />
        </div>
        <div>
            <ScrollArea class="border h-[70vh]">
            <table class="w-full text-center border-collapse">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Role</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(account, accountIndex) in filteredAccounts" :key="accountIndex" style="text-align: center;">
                        <td>{{ account.username }}</td>
                        <td>{{ account.role }}</td>
                        <td> <Button @click="$emit('createAccount', account)"> Manage </Button></td>
                    </tr>
                    </tbody>
                </table>
            </ScrollArea>
        </div>
  </DialogContent>
</template>