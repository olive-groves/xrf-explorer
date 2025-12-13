import { computed, reactive, ref, watch } from "vue";
import { WorkspaceConfig } from "./workspace";
import { Selection } from "./selection";
import { layerGroups } from "@/components/image-viewer/state";

type AreaSelection = {
  type: undefined;
  points: [];
};

const createAreaSelection = (): AreaSelection => ({
  type: undefined,
  points: [],
});

/**
 * Reactive value that contains the current appstate.
 * Use computed() in components to read properties of this state.
 */
export const appState = reactive<AppState>({
  selection: {
    imageViewer: {
      type: undefined,
      points: [],
    },
    elements: [],
    colorSegmentation: {
      elements: Array(1).fill(0),
      enabled: Array(1).fill(false),
      colors: [],
      k: 20,
      thresholds: Array(1).fill(0),
      useAreaSelection: false,
      areaSelection: createAreaSelection(),
      lastCompleteSelectionTimestamp: 0,
      lastColorSegmentationRun: 0,
    },
    dimensionalityReduction: {
      color: "#ffffff",
      area: {
        type: undefined,
        points: [],
      },
    },
    dimensionalityReductionPainting: {
      element: 0,
      useAreaSelection: false,
      areaSelection: createAreaSelection(),
      lastCompleteSelectionTimestamp: 0,
    },
  },
  user: {
    username: "",
    role: "",
    projects: [],
  },
});

/**
 * Deprecated compatibility helpers — prefer `workspace.stitchingMode`.
 */
Object.defineProperty(appState, "stitching", {
  get() {
    return (appState.workspace?.stitchingMode ?? "full") === "partial";
  },
  set(v: boolean) {
    if (!appState.workspace) return;
    appState.workspace.stitchingMode = v ? "partial" : "full";
  },
  configurable: true,
});

/**
 * Some useful variables directly computed from appState.
 * Readonly, for writing you need to directly modify appState.
 */
export const datasource = computed(() => appState.workspace?.name ?? "");
export const elements = computed(
  () => appState.workspace?.elementalChannels.filter((element) => element.enabled) ?? [],
);
export const elementalDataPresent = computed(() => (appState.workspace?.elementalCubes.length ?? 0) > 0);
export const spectralDataPresent = computed(() => (appState.workspace?.spectralCubes.length ?? 0) > 0);
export const pinnedGroups = computed(() => Object.values(layerGroups.value).filter((g) => g.pinned));
/**
 * Positions of pinned groups in the image viewer.
 * @param x X-coordinate of the pinned group position.
 * @param y Y-coordinate of the pinned group position.
 */
export const pinnedGroupPositions = ref<Record<string, { x: number; y: number }>>({});

watch(
  pinnedGroups,
  (groups) => {
    groups.forEach((group) => {
      if (!pinnedGroupPositions.value[group.name]) {
        pinnedGroupPositions.value[group.name] = { x: 0, y: 0 };
      }
    });
  },
  { deep: true },
);

type User = {
  /**
   * The username of the current logged in user.
   */
  username: string;
  /**
   * The role of the current logged in user.
   */
  role: string;
  /**
   * The projects the current logged in user has access to.
   */
  projects: string[];
};

/**
 * Type describing the state of the client.
 * Solely intended for data that needs to be accessed from many different unrelated components.
 */
export type AppState = {
  /**
   * The current workspace.
   */
  workspace?: WorkspaceConfig;
  /**
   * The active selection.
   */
  selection: Selection;
  /**
   * Whether the stitching viewer is enabled.
   */
  // deprecated: keep the property documented for older code paths. Prefer workspace.stitchingMode.
  stitching?: boolean;
  /**
   * The role of the current logged in user.
   */
  user: User;
};
