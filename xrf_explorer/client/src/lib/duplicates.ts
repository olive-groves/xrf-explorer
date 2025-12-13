/**
 * This function returns 3 properties that are shared between colorSegmentation and dimensionalityReductionPainting.
 * @returns An array containing a boolean, an object with type and points properties, and a number.
 */
export function ProvidePropertiesColorSegmentationAndDimensionalityReduction() {
  return [false, { type: undefined, points: [] }, 0];
}
