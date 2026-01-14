<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Eye, EyeOff } from "lucide-vue-next";
import { Input } from "@/components/ui/input";
import { ref, computed, inject } from "vue";
import { toast } from "vue-sonner";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import axios from "axios";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useFetch } from "@vueuse/core";
import { FrontendConfig } from "@/lib/config";
import { validPassword, toggleText } from "./duplicates.ts";

// Define emits
const emit = defineEmits<{
  // Close the dialog
  (e: "close"): void;
  // Delete specific user and pass (original) username
  (e: "deleteAccount", deleteUser: { original_username: string }): void;
}>();

// Define props
const props = defineProps<{
  /** User data passed from the parent. */
  user: { original_username: string; username: string; role: string };
}>();

// Store original username to identify the account to update
const originalUsername = ref(props.user.original_username);
const username = ref(props.user.username); // Selected username
const password = ref(""); // New password (optional)
const role = ref(props.user.role.toLowerCase()); // Selected role
const originalRole = ref(role.value);
const changedAccess = ref(false);

// Search query for filtering projects
const projectQuery = ref("");

// Inject the frontend configuration
const config = inject<FrontendConfig>("config")!;

// Fetch files
const request = useFetch(`${config.api.endpoint}/data_sources`);
const projects = computed(() => {
  return JSON.parse((request.data.value ?? "[]") as string) as string[];
});

// Store projects the user has access to
const accessedProjects = ref<string[]>([]);
void refreshProjects();

// Computed list of projects with access status
const computedProjects = computed(() =>
  projects.value.map((str) => ({
    name: str,
    access: role.value == "admin" || accessedProjects.value.includes(str) ? "Yes" : "No",
  })),
);
const passwordType = ref("password");

/**
 * determines if the update button should be enabled
 */
const determineDisabled = computed(() => {
  if (password.value !== '' && !validPassword(password.value)) {
    return true;
  }

  if (username.value !== originalUsername.value) {
    if (username.value === "") {
      return true;
    }
    return false;
  }

  if (role.value !== originalRole.value) {
    return false;
  }

  console.log(changedAccess.value);
  
  if (changedAccess.value) {
    return false;
  }

  return true;
});

/**
 * Get project access for the user.
 */
async function refreshProjects() {
  const res = await axios.get<string[]>(`/api/projects/${username.value}`);
  accessedProjects.value = res.data;
}

// Interface for API response
interface APIResponse {
  success: boolean;
  message?: string;
}

/**
 * Update the account information.
 */
async function updateAccount() {
  // Check if at least username and role are filled
  if (!username.value || !role.value) {
    toast.error("Username and Role are required");
    return;
  }

  // Make API call to update account
  try {
    const response = await axios.post<APIResponse>("/api/update_account", {
      originalUsername: originalUsername.value,
      username: username.value,
      password: password.value,
      role: role.value.toUpperCase(), // Ensure role is uppercase to match backend enum
    });

    // On success, notify user and emit close; else give error message
    if (response.data.success) {
      toast.info("Account updated successfully");
      emit("close");
    } else {
      toast.error(response.data.message || "Account update failed");
    }
  } catch (error: unknown) {
    toast.error("Account update failed");
  }
}

/**
 * Delete the account.
 */
function deleteAccount() {
  emit("deleteAccount", { original_username: originalUsername.value });
}

// Filter logic
const filteredProjects = computed(() => {
  const query = projectQuery.value.toLowerCase().trim();
  if (!query) return computedProjects.value;
  return computedProjects.value.filter(
    (a) => a.name.toLowerCase().includes(query) || a.access.toLowerCase().includes(query),
  );
});

/**
 * Give access to a project.
 * @param projectName The project to give access to.
 */
async function giveAccess(projectName: string) {
  try {
    const response = await axios.post<APIResponse>("/api/grant_project_access", {
      username: username.value,
      project: projectName,
    });

    // On success, notify user; else give error message
    if (response.data.success) {
      toast.info("Access granted successfully");
      changedAccess.value = true;
      await refreshProjects();
    } else {
      toast.error(response.data.message || "Grant Access failed");
    }
  } catch (error: unknown) {
    toast.error("Grant Access failed");
  }
}

/**
 * Give access to all projects.
 */
async function giveAccessAll() {
  if (role.value == "admin") {
    toast.error("Admins have access to all projects by default");
    return;
  } else {
    for (const project of projects.value) {
      if (!accessedProjects.value.includes(project)) await giveAccess(project);
    }
    changedAccess.value = true;
  }
}

// Remove access to a project
/**
 * Remove access to a project.
 * @param projectName The project to remove access from.
 */
async function removeAccess(projectName: string) {
  if (role.value == "admin") {
    toast.error("Admins have access to all projects by default");
    return;
  }
  try {
    const response = await axios.post<APIResponse>("/api/revoke_project_access", {
      username: username.value,
      project: projectName,
    });

    // On success, notify user; else give error message
    if (response.data.success) {
      toast.info("Access revoked successfully");
      changedAccess.value = true;
      await refreshProjects();
    } else {
      toast.error(response.data.message || "Revoke Access failed");
    }
  } catch (error: unknown) {
    toast.error("Revoke Access failed");
  }
}

/**
 * Remove access to all projects.
 */
async function removeAccessAll() {
  if (role.value == "admin") {
    toast.error("Admins have access to all projects by default");
    return;
  } else {
    for (const project of projects.value) {
      if (accessedProjects.value.includes(project)) await removeAccess(project);
    }
    changedAccess.value = true;
  }
}
</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Update Account </DialogTitle>
    <!-- Input fields -->
    <div class="text-base">Username</div>
    <Input placeholder="Username" v-model:model-value="username" />
    <div class="text-base">Password (leave empty to keep current password)</div>
    <div class="flex items-center">
      <Input placeholder="New Password" :type="passwordType" v-model:model-value="password" />
      <Button
        @click="passwordType = toggleText(passwordType)"
        variant="ghost"
        class="size-8 p-2"
        title="Toggle visibility"
      >
        <Eye v-if="passwordType === 'password'" />
        <EyeOff v-else />
      </Button>
    </div>
    <div v-if="!(password.length >= 12 && password.length <= 32)" class="text-muted-foreground">
      *Password must be between 12 and 32 characters
    </div>
    <div v-if="!/[0-9]/.test(password)" class="text-muted-foreground">
      *Password must include at least one number (0-9)
    </div>
    <div v-if="!/[!@#$%^&*]/.test(password)" class="text-muted-foreground">
      *Password must include at least one special character (!@#$%^&*)
    </div>
    <Select v-model="role" class="mb-4 w-full">
      <!-- Dropdown for role select -->
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
    <div>
      <Input v-model="projectQuery" placeholder="Search by project or access..." />
    </div>
    <div>
      <!-- Scrollbar -->
      <ScrollArea class="h-[40vh] border">
        <!-- Table of user data from the database -->
        <table class="w-full border-collapse text-center">
          <thead>
            <th><Button @click="giveAccessAll"> Give access to all </Button></th>
            <th></th>
            <th><Button @click="removeAccessAll"> Remove access from all </Button></th>
            <tr>
              <th>Project</th>
              <th>Access?</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(project, projectIndex) in filteredProjects" :key="projectIndex" style="text-align: center">
              <td>{{ project.name }}</td>
              <td :class="project.access === 'Yes' ? 'text-green-600' : 'text-red-600'">{{ project.access }}</td>
              <td>
                <Button v-if="project.access == 'No'" @click="giveAccess(project.name)"> Give access </Button>
                <Button v-if="project.access == 'Yes'" @click="removeAccess(project.name)"> Remove access </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </ScrollArea>
    </div>
    <div class="flex items-center justify-between">
      <Button @click="emit('close')"> Cancel </Button>
      <Button @click="updateAccount" :disabled=determineDisabled>
        Update Account
      </Button>
      <Button @click="deleteAccount" variant="destructive"> Delete Account </Button>
    </div>
  </DialogContent>
</template>
