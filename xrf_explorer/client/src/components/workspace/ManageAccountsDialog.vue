<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ref, computed, onMounted } from "vue";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import axios from "axios";
// import { toast } from "vue-sonner";

// Define emits
const emit = defineEmits<{
    (e: 'close'): void, // Close the dialog
    (e: 'createAccount'): void, // Open Create Account dialog
    (e: 'manageUser', account: {original_username: string, username: string; role: string}): void // Manage specific user and pass data
}>();

// Search query for filtering accounts
const searchQuery = ref("");

// Stored accounts from backend
interface Account {
  username: string;
  role: string;
}

// All accounts fetched from backend
const storedAccounts = ref<Account[]>([]);

// Fetch accounts on component mount
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

// Emit manage user event with relevant data
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
         <!-- Search bar -->
        <div>
            <Input
                v-model="searchQuery"
                placeholder="Search by username or role..."
            />
        </div>
        <div>
          <!-- Scrollbar -->
            <ScrollArea class="border h-[70vh]">
              <!-- Table of user data from the database -->
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