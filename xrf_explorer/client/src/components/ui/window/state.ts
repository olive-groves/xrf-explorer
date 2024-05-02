import { reactive } from 'vue';

export type WindowState = {
    title: string,
    opened: boolean
};

export const window_state = reactive<{
    [key: string]: WindowState
}>({});