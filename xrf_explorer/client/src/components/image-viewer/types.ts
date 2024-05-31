import * as THREE from "three";

/**
 * Type describing a layer in the layer system.
 */
export type Layer = {
  /**
   * The id of the layer.
   */
  id: string;
  /**
   * An identifier for the image associated with the layer.
   */
  image: string;
  /**
   * The mesh describing the layer in the THREE scene.
   */
  mesh?: THREE.Mesh;
  /**
   * The uniforms associated with the layer.
   */
  uniform: LayerUniform;
};

/**
 * Type containing the uniforms necessary to render each of the layers.
 */
export type LayerUniform = {
  /**
   * The index of the layer, determines which layers are rendered above which other layers.
   */
  iIndex: { value: number };
  /**
   * The type of the layer, determines how the shader uses auxiliary data to render the layer.
   */
  iLayerType: { value: LayerType };
  /**
   * Contains a single number of auxiliary data.
   */
  iAuxiliary?: { value: number };
  /**
   * Contains a data texture of auxiliary data.
   */
  tAuxiliary?: { value: THREE.Texture; type: "t" };
  /**
   * The current size and location of the viewport.
   */
  iViewport: { value: THREE.Vector4 };
  /**
   * The texture of the image associated with the layer.
   */
  tImage?: { value: THREE.Texture; type: "t" };
  /**
   * The 3x3 matrix describing the perspective transform for registering.
   */
  mRegister: { value: THREE.Matrix3 };
  /**
   * Determines the visibility of the layer in the image viewer.
   */
  iShowLayer: { value: LayerVisibility };
  /**
   * The opacity that the layer should be drawn at.
   */
  uOpacity: { value: number };
  /**
   * The contrast that the layer should be drawn at.
   */
  uContrast: { value: number };
  /**
   * The saturation that the layer should be drawn at.
   */
  uSaturation: { value: number };
  /**
   * The gamma that the layer should be drawn at.
   */
  uGamma: { value: number };
  /**
   * The brightness that the layer should be drawn at.
   */
  uBrightness: { value: number };
  /**
   * The location of the mouse in WebGL coordinates.
   */
  uMouse: { value: THREE.Vector2 };
  /**
   * The radius of the lens.
   */
  uRadius: { value: number };
};

/**
 * Type describing the current state of the toolbar.
 */
export type ToolState = {
  /**
   * The currently active tool.
   */
  tool: Tool;
  /**
   * The amount by which the panning speed is multiplied in the image viewer.
   */
  movementSpeed: number[];
  /**
   * The amount by which the zooming speed is multiplied in the image viewer.
   */
  scrollSpeed: number[];
  /**
   * The amount used to determine the lens size.
   */
  lensSize: number[];
};

/**
 * The different tools in the image viewer.
 */
export type Tool = "grab" | "lens" | "lasso";

/**
 * Type describing a group of layers as used in the LayerSystem.
 */
export type LayerGroup = {
  /**
   * The name of this group of layers.
   */
  name: string;
  /**
   * An additional description for the group of layers.
   */
  description: string;
  /**
   * The layers that this group represents.
   */
  layers: Layer[];
  /**
   * The index of this group of layers.
   */
  index: number;
  /**
   * Determines whether the layers in this group are visible.
   */
  visible: boolean;
  /**
   * Determines where the layers in this group are visible.
   */
  visibility: LayerVisibility;
  /**
   * Opacity of the layers in this group.
   */
  opacity: number[];
  /**
   * Contrast of the layers in this group.
   */
  contrast: number[];
  /**
   * Saturation of the layers in this group.
   */
  saturation: number[];
  /**
   * Gamma of the layers in this group.
   */
  gamma: number[];
  /**
   * Brightness of the layers in this group.
   */
  brightness: number[];
};

/**
 * Indicates the visibility of a layer(group).
 */
export enum LayerVisibility {
  Invisible = 0,
  Visible = 1,
  InsideLens = 2,
  OutsideLens = 3,
}

/**
 * Indicates the type of a layer.
 */
export enum LayerType {
  Image = 0,
  Elemental = 1,
  ColorSegmentation = 2,
  DimensionalityReduction = 3,
}

/**
 * Represent a point in 2D space.
 */
export type Point2D = {
  /**
   * Represents the X coordinate of the point.
   */
  x: number;
  /**
   * Represents the Y coordinate of the point.
   */
  y: number;
};
