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
  url: string;
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
};

/**
 * Type describing the current state of the toolbar.
 */
export type ToolState = {
  /**
   * The amount by which the panning speed is multiplied in the image viewer.
   */
  movementSpeed: number[];
  /**
   * The amount by which the zooming speed is multiplied in the image viewer.
   */
  scrollSpeed: number[];
};

/**
 * Type describing a group of layers as used in the LayerSystem.
 */
export type LayerGroup = {
  /**
   * The type of this layer group.
   */
  type: "base" | "contextual" | "elemental" | "colorSegmentation" | "dimensionalityReduction";
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
   * Determines whether the layers in this group are visible.
   */
  visible: boolean;
  /**
   * Determines where the layers in this group are visible.
   */
  visibility: LayerVisibility;
};

/**
 * Indicates the visibility of a layer(group).
 * 1: Visible inside of lens.
 * 2: Visible outside of lens.
 * 3: Completely visible.
 */
export type LayerVisibility = 1 | 2 | 3;
