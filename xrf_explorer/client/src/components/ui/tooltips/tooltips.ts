import type { Directive } from "vue";
import { getTooltipByKey } from "@/lib/useToolTips";

/**
 * Tooltip bound for vue components. Usage: v-tooltip([path in json file]).
 */
export const vTooltip: Directive = {
  mounted(el, binding) {
    const key = binding.value;
    const text = getTooltipByKey(key);
    el.setAttribute("title", text);
  },
  updated(el, binding) {
    const key = binding.value;
    const text = getTooltipByKey(key);
    el.setAttribute("title", text);
  },
};
