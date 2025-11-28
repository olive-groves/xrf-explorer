<script setup lang="ts">
// Import the necessary components
import { reactive, ref } from "vue";
import { pinnedGroups } from "@/lib/appState";
import { ImageViewer } from ".";
import { PinnedLayerCard } from "@/components/ui/slider";

// State to track dragging
const draggingCard = ref<null | {
  groupName: string;
  offsetX: number;
  offsetY: number;
}>(null);

const movedCards = reactive(new Map<string, boolean>());

// Event handlers
/**
 * Handles the mouse down event on a card to initiate dragging.
 * @param event The mouse event.
 * @param groupName The name of the group associated with the card.
 */
function onMouseDownCard(event: MouseEvent, groupName: string) {
  event.preventDefault();
  const target = event.currentTarget as HTMLElement;
  const rect = target.getBoundingClientRect();
  draggingCard.value = {
    groupName,
    offsetX: event.clientX - rect.left,
    offsetY: event.clientY - rect.top,
  };
}

/**
 * Handles the mouse move event to update the position of the dragged card.
 * @param event The mouse event.
 */
function onMouseMoveCard(event: MouseEvent) {
  if (!draggingCard.value) return;

  const group = draggingCard.value.groupName;
  const cardEl = document.querySelector<HTMLElement>(`[data-group-name="${group}"]`);
  if (!cardEl) return;

  // Parent container that has the transform
  const parent = cardEl.offsetParent as HTMLElement;
  const parentRect = parent.getBoundingClientRect();

  // Calculate position relative to the parent container
  const x = event.clientX - draggingCard.value.offsetX - parentRect.left;
  const y = event.clientY - draggingCard.value.offsetY - parentRect.top;

  cardEl.style.position = "absolute";
  cardEl.style.left = `${x}px`;
  cardEl.style.top = `${y}px`;
  cardEl.style.zIndex = "1000";

  movedCards.set(group, true);
}

/**
 * Handles the mouse up event to stop dragging.
 */
function onMouseUpCard() {
  draggingCard.value = null;
}

/**
 * Handles unpinning of a layer group.
 * @param groupName The name of the group to unpin.
 */
function onUnpin(groupName: string) {
  // Debug log: show the item in movedCards before deletion
  console.debug("Moved cards before unpin:", Array.from(movedCards.keys()));
  const group = pinnedGroups.value.find((g) => g.name === groupName);
  if (group) {
    group.pinned = false;
  }
  movedCards.delete(groupName);
  // debug log: show the item in movedCards after deletion
  console.debug("Moved cards after unpin:", Array.from(movedCards.keys()));

  const cardEl = document.querySelector<HTMLElement>(`[data-group-name="${groupName}"]`);
  if (cardEl) {
    cardEl.style.position = "";
    cardEl.style.left = "";
    cardEl.style.top = "";
    cardEl.style.zIndex = "";
  }
}
</script>

<template>
  <div class="size-full" @mousemove="onMouseMoveCard" @mouseup="onMouseUpCard">
    <ImageViewer />
    <div v-if="pinnedGroups.length" class="absolute left-1/2 top-2 z-50 flex -translate-x-1/2 space-x-2">
      <PinnedLayerCard
        v-for="group in pinnedGroups.filter((g) => !movedCards.get(g.name))"
        :key="group.name"
        :group="group"
        :data-group-name="group.name"
        @unpin="onUnpin(group.name)"
        @mousedown="(event: MouseEvent) => onMouseDownCard(event, group.name)"
      />
    </div>

    <!-- FLOATING LAYER: cards that HAVE been moved -->
    <div class="absolute left-0 top-0 z-50">
      <PinnedLayerCard
        v-for="group in pinnedGroups.filter((g) => movedCards.get(g.name))"
        :key="group.name + '-floating'"
        :group="group"
        :data-group-name="group.name"
        @unpin="onUnpin(group.name)"
        @mousedown="(e: MouseEvent) => onMouseDownCard(e, group.name)"
      />
    </div>
  </div>
</template>
