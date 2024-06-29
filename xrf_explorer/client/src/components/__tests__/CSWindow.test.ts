import { shallowMount } from "@vue/test-utils";
import CSWindow from "@/windows/CSWindow.vue";
import { describe, expect, it } from "vitest";

describe("CSWindow", () => {
  it("renders the component", () => {
    const wrapper = shallowMount(CSWindow);
    expect(wrapper.exists()).toBe(true);
  });

  it("fetches colors when generate button is clicked", async () => {
    const fetchColors = jest.fn();
    const wrapper = shallowMount(CSWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        provide: {
          fetchColors,
        },
      },
    });

    await wrapper.find("button").trigger("click");

    expect(fetchColors).toHaveBeenCalled();
  });

  it("updates the CS selection when generate button is clicked", async () => {
    const updateSelection = jest.fn();
    const wrapper = shallowMount(CSWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        provide: {
          updateSelection,
        },
      },
    });

    await wrapper.find("button").trigger("click");

    expect(updateSelection).toHaveBeenCalled();
  });

  it("toggles the cluster when a color is clicked", async () => {
    const toggleCluster = jest.fn();
    const wrapper = shallowMount(CSWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        provide: {
          toggleCluster,
        },
      },
    });

    await wrapper.find(".color-palette").trigger("click");

    expect(toggleCluster).toHaveBeenCalled();
  });
});