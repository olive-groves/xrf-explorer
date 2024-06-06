<script setup lang="ts">
import { type HTMLAttributes, computed, inject, provide } from "vue";
import {
  DialogClose,
  DialogContent,
  type DialogContentEmits,
  type DialogContentProps,
  DialogOverlay,
  DialogPortal,
  useForwardPropsEmits,
} from "radix-vue";
import { Cross2Icon } from "@radix-icons/vue";
import { cn } from "@/lib/utils";

const props = defineProps<
  DialogContentProps & {
    // eslint-disable-next-line vue/require-prop-comment
    class?: HTMLAttributes["class"];
  }
>();
const emits = defineEmits<DialogContentEmits>();

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props;

  return delegated;
});

const dialogOverlay = inject<boolean>("dialogOverlay") ?? false;
provide("dialogOverlay", true);

const forwarded = useForwardPropsEmits(delegatedProps, emits);
</script>

<template>
  <DialogPortal>
    <DialogOverlay
      :class="{
        'bg-black/80': !dialogOverlay,
      }"
      class="fixed inset-0 z-50 grid place-items-center overflow-y-auto data-[state=open]:animate-in
        data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
    >
      <DialogContent
        :aria-describedby="undefined"
        :class="
          cn(
            `relative z-50 grid w-full max-w-lg my-8 gap-2 border border-border bg-background p-4 shadow-lg duration-200
            sm:rounded-lg md:w-full`,
            props.class,
          )
        "
        v-bind="forwarded"
        @pointer-down-outside="
          (event) => {
            const originalEvent = event.detail.originalEvent;
            const target = originalEvent.target as HTMLElement;
            if (originalEvent.offsetX > target.clientWidth || originalEvent.offsetY > target.clientHeight) {
              event.preventDefault();
            }
          }
        "
      >
        <slot />

        <DialogClose class="absolute right-4 top-4 rounded-md p-0.5 transition-colors hover:bg-secondary">
          <Cross2Icon class="size-4" />
          <span class="sr-only">Close</span>
        </DialogClose>
      </DialogContent>
    </DialogOverlay>
  </DialogPortal>
</template>
