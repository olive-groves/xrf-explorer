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
  contextualLayers: ContextualImage[];
  /**
   * All spectral cubes in the workspace.
   */
  spectralCubes: SpectralCube[];
  /**
   * All elemental cubes in the workspace.
   */
  elementalCubes: ElementalCube[];
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
   * A unique id for the spectral cube.
   */
  id: string;
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
   * A unique id for the spectral cube.
   */
  id: string;
  /**
   * The location of the raw data file, used by the backend.
   */
  dmsLocation: string;
  /**
   * The location of the registering recipe, used by the backend.
   */
  recipeLocation: string;
};
