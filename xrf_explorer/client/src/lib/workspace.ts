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
   * All color clusters present in the whole image.
   */
  colorClusters: ColorCluster;
  /**
   * All the color clusters present per element.
   */
  elementColorClusters: ElementColorCluster[];
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

/**
 * Describes the configuration for the full-image color clusters.
 */
export type ColorCluster = {
  /**
   * The name of the cluster.
   */
  name: string;
  /**
   * Should the clusters be visible to the client.
   */
  enable: boolean;
  /**
   * The index of the cluster (if any) that should be visible to the client.
   */
  chosenCluster: number;
}

/**
 * Describes the configuration for the color clusters of a 
 * single element.
 */
export type ElementColorCluster = {
  /**
   * The name of the clusters.
   */
  name: string;
  /**
   * The index of the corresponding elemental channel.
   */
  channel: number;
  /**
   * Should the clusters be visible to the client.
   */
  enabled: boolean;
  /**
   * The index of the cluster (if any) that should be visible to the client.
   */
  chosenCluster: number;
}
