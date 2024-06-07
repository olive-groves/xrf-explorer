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
   * All elemental cubes in the workspace.
   */
  elementalCubes: ElementalCube[];
  /**
   * All elemental channels present in the elemental cubes.
   */
  elementalChannels: ElementalChannel[];
  /**
   * The parameters to read the spectral data
   */
  spectralParams: SpectralParams;
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
   * The location of the registering recipe, used by the backend.
   */
  recipeLocation: string;
};

export type SpectralParams = {
  /**
   * The lower channel boundary to be used
   */
  low: number;
  /**
   * The higher channel boundary to be used
   */
  high: number;
  /**
   * The bin size to be used while reading the raw data
   */
  binSize: number;
};

/**
 * Represents an elemental datacube.
 */
export type ElementalCube = {
  /**
   * A unique name for the spectral cube.
   */
  name: string;
  /**
   * The filetype for the elemental data cube.
   */
  fileType: ElementalCubeFileType;
  /**
   * The location of the raw data file, used by the backend.
   */
  dataLocation: string;
  /**
   * The location of the registering recipe, used by the backend.
   */
  recipeLocation: string;
};

/**
 * The different elemental cube formats that we can handle.
 */
export type ElementalCubeFileType = "csv" | "dms";

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
