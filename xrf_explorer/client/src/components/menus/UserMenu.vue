<script setup lang="ts">
import { MenubarMenu, MenubarTrigger, MenubarContent, MenubarItem } from "@/components/ui/menubar";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { LoginDialog, LogoutDialog, CreateAccountDialog, ManageAccountsDialog } from "@/components/workspace";
import { ref } from "vue";
import { appState } from "@/lib/appState";

// Dialog visibility variable
const dialogOpen = ref(false);

// Which window to open
const window = ref("");

// References to child components
const LoginRef = ref();
const CreateAccountRef = ref();

// Reset the dialog state on close
function reset() {
  if (LoginRef.value && LoginRef.value.resetFields) {
    LoginRef.value.resetFields();
  }
  if (CreateAccountRef.value && CreateAccountRef.value.resetFields) {
    CreateAccountRef.value.resetFields();
  }
  window.value = "";
}

</script>
<template>
  <Dialog v-model:open="dialogOpen" @update:open="reset">
    <MenubarMenu>
      <MenubarTrigger> Users </MenubarTrigger>
      <MenubarContent>
        <DialogTrigger v-if="appState.userRole == ''" class="w-full" @click="window = 'login'"><MenubarItem>Log in</MenubarItem></DialogTrigger>
        <DialogTrigger v-if="appState.userRole != ''" class="w-full" @click="window = 'logout'"><MenubarItem>Log out</MenubarItem></DialogTrigger>
        <DialogTrigger v-if="appState.userRole == 'ADMIN'" class="w-full" @click="window = 'manage-accounts'"><MenubarItem>Manage Accounts</MenubarItem></DialogTrigger>
      </MenubarContent>
    </MenubarMenu>
    <LoginDialog ref="LoginRef" v-if="window == 'login'" @close="dialogOpen = false" />
    <LogoutDialog v-if="window == 'logout'" @close="dialogOpen = false" />
    <ManageAccountsDialog v-if="window == 'manage-accounts'" @close="dialogOpen = false" @create-account="window = 'create-account'" />
    <CreateAccountDialog ref="CreateAccountRef" v-if="window == 'create-account'" @close="dialogOpen = false" />
  </Dialog>
</template>