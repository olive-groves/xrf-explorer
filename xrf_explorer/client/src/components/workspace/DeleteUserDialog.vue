<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ref} from "vue";
import { toast } from "vue-sonner";

// Define emits
const emit = defineEmits(["close"]);
const props = defineProps<{
    user: string;
}>();

// Define user to delete
const user = ref(props.user);

// On deletion, notify the user and emit close event
function deleteUser() {
    user.value = "";
    toast.info(`User ${props.user} deleted successfully`);
    emit("close");
}

</script>

<template>
  <DialogContent ref="dialog">
    <DialogTitle class="mb-2 font-bold"> Log out </DialogTitle>
    <div class="flex items-center justify-between">
        <div class="text-muted-foreground">Are you sure you want to delete the following account: {{ user }} ?</div>
        <Button @click="deleteUser" >
            Delete
        </Button>
    </div>
  </DialogContent>
</template>