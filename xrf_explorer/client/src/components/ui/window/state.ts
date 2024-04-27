import { reactive } from 'vue';

export const window_state = reactive<{
    windows: {
        [key: string]: {
            is_opened: boolean,
            z_index: number
        }
    }
}>({
    windows: {}
})