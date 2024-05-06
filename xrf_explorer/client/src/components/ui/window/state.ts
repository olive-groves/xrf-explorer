import { reactive } from 'vue';

export type WindowState = {
    id: string,
    title: string,
    opened: boolean,
    portalMounted: boolean
};

export const window_state = reactive<{
    [key: string]: WindowState
}>({});