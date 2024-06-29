<script setup lang="ts">
import { shallowMount } from "@vue/test-utils";
import ChartWindow from "@/windows/ChartWindow.vue";

describe("ChartWindow", () => {
  it("renders the component", () => {
    const wrapper = shallowMount(ChartWindow);
    expect(wrapper.exists()).toBe(true);
  });

  it("fetches global averages on window mount", async () => {
    const fetchGlobalAverages = jest.fn();
    const wrapper = shallowMount(ChartWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        stubs: ["Window"],
        provide: {
          fetchGlobalAverages,
        },
      },
    });

    await wrapper.vm.setupWindow();

    expect(fetchGlobalAverages).toHaveBeenCalled();
  });

  it("updates charts when workspace elements are updated", async () => {
    const updateCharts = jest.fn();
    const wrapper = shallowMount(ChartWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        stubs: ["Window"],
        provide: {
          updateCharts,
        },
      },
    });

    await wrapper.vm.$nextTick();

    expect(updateCharts).toHaveBeenCalled();
  });

  it("updates charts when element selection is updated", async () => {
    const updateCharts = jest.fn();
    const wrapper = shallowMount(ChartWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        stubs: ["Window"],
        provide: {
          updateCharts,
        },
      },
    });

    await wrapper.vm.$nextTick();

    expect(updateCharts).toHaveBeenCalled();
  });

  it("fetches selection averages when area selection is updated", async () => {
    const fetchSelectionAverages = jest.fn();
    const wrapper = shallowMount(ChartWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        stubs: ["Window"],
        provide: {
          fetchSelectionAverages,
        },
      },
    });

    await wrapper.vm.onSelectionAreaUpdate({ x: 0, y: 0, width: 100, height: 100 });

    expect(fetchSelectionAverages).toHaveBeenCalled();
  });

  it("clears the chart when area selection is cancelled", async () => {
    const clearChart = jest.fn();
    const wrapper = shallowMount(ChartWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        stubs: ["Window"],
        provide: {
          clearChart,
        },
      },
    });

    await wrapper.vm.onSelectionAreaUpdate(undefined);

    expect(clearChart).toHaveBeenCalled();
  });

  it("fetches averages when datasource is selected", async () => {
    const fetchAverages = jest.fn();
    const wrapper = shallowMount(ChartWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        stubs: ["Window"],
        provide: {
          fetchAverages,
        },
      },
    });

    wrapper.vm.$data.datasource = "example-datasource";
    await wrapper.vm.$nextTick();

    expect(fetchAverages).toHaveBeenCalled();
  });

  it("does not fetch averages when no datasource is selected", async () => {
    const fetchAverages = jest.fn();
    const wrapper = shallowMount(ChartWindow, {
      global: {
        mocks: {
          $nextTick: jest.fn(),
        },
        stubs: ["Window"],
        provide: {
          fetchAverages,
        },
      },
    });

    wrapper.vm.$data.datasource = "";
    await wrapper.vm.$nextTick();

    expect(fetchAverages).not.toHaveBeenCalled();
  });
});
</script>
