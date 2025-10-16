<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ref, computed, onMounted } from "vue";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import axios from "axios";
// import { toast } from "vue-sonner";

const emit = defineEmits<{
    (e: 'close'): void, 
    (e: 'createAccount'): void, 
    (e: 'manageUser', account: {original_username: string, username: string; role: string}): void
}>();

const searchQuery = ref("");

const username = ref("");
const password = ref("");
const role = ref("");

interface Account {
  username: string;
  role: string;
}

const storedAccounts = ref<Account[]>([]);

onMounted(async () => {
  try {
    const response = await axios.get<Account[]>('/api/accounts');
    storedAccounts.value = response.data;
  } catch (error) {
    console.error("Failed to fetch accounts", error);
  }
});

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

function resetFields() {
    username.value = "";
    password.value = "";
    role.value = "";
}
defineExpose({ resetFields });

function manageUser(original_username: string, username: string, role: string) {
    emit("manageUser", {original_username, username, role});
}


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
                        <td> <Button @click="manageUser(account.username, account.username, account.role)"> Manage </Button></td>
                    </tr>
                    </tbody>
                </table>
            </ScrollArea>
        </div>
  </DialogContent>
</template>