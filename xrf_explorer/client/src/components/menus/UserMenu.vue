<script setup lang="ts">
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarItem } from "@/components/ui/menubar";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import {
  LoginDialog,
  LogoutDialog,
  CreateAccountDialog,
  ManageAccountsDialog,
  ManageUserDialog,
  DeleteUserDialog,
} from "@/components/workspace";
import { ref } from "vue";
import { appState } from "@/lib/appState";

// Dialog visibility variable
const dialogOpen = ref(false);

// Which window to open
const window = ref("");

// References to child components
const LoginRef = ref();
const CreateAccountRef = ref();

// User data for managing users
const originalName = ref("");
const userName = ref("");
const userRole = ref("");

// Reset the dialog state on close
function reset() {
  if (LoginRef.value && LoginRef.value.resetFields) {
    // Reset Login fields
    LoginRef.value.resetFields();
  }
  if (CreateAccountRef.value && CreateAccountRef.value.resetFields) {
    // Reset Create Account fields
    CreateAccountRef.value.resetFields();
  }
  window.value = "";
}

// When managing a specific user, pass relevant data from ManageAccountsDialog
function manageUser(account: { original_username: string; username: string; role: string }) {
  window.value = "manage-user";
  originalName.value = account.original_username;
  userName.value = account.username;
  userRole.value = account.role;
}
</script>
<template>
  <Dialog v-model:open="dialogOpen" @update:open="reset">
    <MenubarMenu>
      <MenubarTrigger> {{ appState.user.role != "" ? appState.user.username : "Log in" }} </MenubarTrigger>
      <MenubarContent>
        <!-- Display login/logout depending on login status and Manage Accounts if the current user is an Admin -->
        <DialogTrigger v-if="appState.user.role == ''" class="w-full" @click="window = 'login'">
          <MenubarItem>Log in</MenubarItem>
        </DialogTrigger>
        <DialogTrigger v-if="appState.user.role != ''" class="w-full" @click="window = 'logout'">
          <MenubarItem>Log out</MenubarItem>
        </DialogTrigger>
        <DialogTrigger v-if="appState.user.role == 'ADMIN'" class="w-full" @click="window = 'manage-accounts'">
          <MenubarItem>Manage Accounts</MenubarItem>
        </DialogTrigger>
      </MenubarContent>
    </MenubarMenu>
    <!-- Show the relevant window based on "window" and pass data on emits -->
    <LoginDialog ref="LoginRef" v-if="window == 'login'" @close="dialogOpen = false" />
    <LogoutDialog v-if="window == 'logout'" @close="dialogOpen = false" />
    <ManageAccountsDialog
      v-if="window == 'manage-accounts'"
      @close="dialogOpen = false"
      @create-account="window = 'create-account'"
      @manage-user="manageUser"
    />
    <CreateAccountDialog ref="CreateAccountRef" v-if="window == 'create-account'" @close="window = 'manage-accounts'" />
    <ManageUserDialog
      v-if="window == 'manage-user'"
      :user="{ original_username: originalName, username: userName, role: userRole }"
      @close="(window = 'manage-accounts'), (originalName = ''), (userName = ''), (userRole = '')"
      @delete-account="window = 'delete-account'"
    />
    <DeleteUserDialog
      v-if="window == 'delete-account'"
      :user="originalName"
      @close="(window = 'manage-accounts'), (originalName = ''), (userName = ''), (userRole = '')"
    />
  </Dialog>
</template>
