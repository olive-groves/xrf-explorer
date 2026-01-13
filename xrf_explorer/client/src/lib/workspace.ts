import { StitchPoint } from "@/components/image-viewer/stitchPoints";

/**
 * Type describing the workspace and all relevant files in it.
 */
export type WorkspaceConfig = {
  /**
   * The name of the workspace/datasource.
   */
  name: string;
  /**
   * The base image that all other data will be registered to.
   */
  baseImage: ContextualImage;
  /**
   * All contextual images in the workspace.
   */
  contextualImages: ContextualImage[];
  /**
   * All spectral cubes in the workspace.
   */
  spectralCubes: SpectralCube[];
  /**
   * All partial spectral cubes in the workspace.
   */
  partialSpectralCubes: SpectralCube[];
  /**
   * All elemental cubes in the workspace.
   */
  elementalCubes: ElementalCube[];
  /**
   * All partial elemental cubes in the workspace.
   */
  partialElementalCubes: ElementalCube[];
  /**
   * All elemental channels present in the elemental cubes.
   */
  elementalChannels: ElementalChannel[];
  /**
   * All grayscale images generated from the cubes.
   */
  grayscale: Grayscale[];
  /**
   * The parameters to read the spectral data.
   */
  spectralParams: SpectralParams;
  /**
   * Optional stitching mode for this workspace.
   * When set to 'partial' the stitching UI is active.
   */
  stitchingMode: "partial" | "full";
  /**
   * The mapping made by the user for stitching data cubes
   */
  mapping: StitchMapping;
};

/**
 * Represent a contextual image.
 */
export type ContextualImage = {
  /**
   * The name of the contextual image.
   */
  name: string;
  /**
   * The location of the image file, used by the backend.
   */
  imageLocation: string;
  /**
   * The location of the registering recipe, used by the backend.
   * Empty string indicates that the image should not be registered.
   */
  recipeLocation: string;
};

/**
 * Represent a grayscale image.
 */
export type Grayscale = {
  /**
   * The location of the grayscale image.
   */
  imageLocation: string;
  /**
   * The name of the cube that generated this grayscale image.
   */
  sourceCubeName: string;
  /**
   * The type of cube that generated this grayscale image: 'elemental' | 'spectral'
   */
  sourceCubeType: "elemental" | "spectral";
};

/**
 * Represents a spectral datacube.
 */
export type SpectralCube = {
  /**
   * A unique name for the spectral cube.
   */
  name: string;
  /**
   * The location of the raw data file, used by the backend.
   */
  rawLocation: string;
  /**
   * The location of the rpl file, used by the backend.
   */
  rplLocation: string;
  /**
   * The location of the registering recipe of the spectral cube, used by the backend.
   */
  recipeLocation: string;
};

/**
 * Parameters to read the data cube.
 */
export type SpectralParams = {
  /**
   * The lower channel boundary to be used.
   */
  low: number;
  /**
   * The higher channel boundary to be used.
   */
  high: number;
  /**
   * The bin size to be used while reading the raw data.
   */
  binSize: number;
  /**
   * The offset mapping the channels to the right eV.
   */
  offset: number;
  /**
   * Indicating whether the data has already been binned.
   */
  binned: boolean;
};

/**
 * Represents an elemental datacube.
 */
export type ElementalCube = {
  /**
   * A unique name for the elemental cube.
   */
  name: string;
  /**
   * The location of the dms data file, used by the backend.
   */
  dataLocation: string;
  /**
   * The location of the registering recipe of the elemental cube, used by the backend.
   */
  recipeLocation: string;
};

/**
 * Describes the configuration for each elemental channel.
 */
export type ElementalChannel = {
  /**
   * The name of the channel.
   */
  name: string;
  /**
   * The index of the channel.
   */
  channel: number;
  /**
   * Should the channel be visible to the client.
   */
  enabled: boolean;
};

/**
 * Stores the mapping points and rotations made by the user
 */
export type StitchMapping = {
  // Points per grayscale, keyed by grayscale index
  grayscalePoints: Record<number, StitchPoint[]>;
  // Rotation per grayscale
  grayscaleRotation: Record<number, number>;
  // Intensity per greysclae
  grayscaleContrast: Record<number, number>;
  // Wether we are in edit or preview mode
  mode: "edit" | "preview";
}
