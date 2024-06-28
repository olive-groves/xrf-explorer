import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Window from '../ui/window/Window.vue'

describe('Winow.vue Test', () => {
    it('renders props.title when passed', async () => {
        expect(Window).toBeTruthy();

        // render the component
        const wrapper = mount(Window, {
            props: {
                title: 'MyWindow',
                disabled: false,
                opened: true,
                noscroll: false
            }
        })

        console.log(wrapper.emitted())
        // expect(wrapper.emmitted()).toBeTruthy();
        


        // check the title of the component is rendered
        // console.log("Text: ", wrapper)
        // expect(wrapper.text()).toContain('No workspace loaded yet.')
    })
})