import { reactive } from "vue"

export type DialogState = {
    open: boolean
}

export const dialogState = reactive<{
    [key: string]: DialogState
}>({})