import { ElementalCube, SpectralCube, WorkspaceConfig } from "@/lib/workspace";
import { config } from "@/main";

/**
 * Validates a workspace to test if it is sufficient.
 * @param workspace - The workspace to validate.
 * @returns A boolean indicating if the workspace is correct and a possible error message.
 */
export function validateWorkspace(workspace: WorkspaceConfig): [boolean, string] {
  const [isValid, errorMessage] = validateWorkspaceHelper(workspace);
  if (!isValid) {
    return [false, errorMessage];
  }

  // --- Validate full cubes ---
  let [ok, msg] = validateCubes(workspace.spectralCubes, "Spectral", false, workspace);
  if (!ok) return [false, msg];
  [ok, msg] = validateCubes(workspace.elementalCubes, "Elemental", false, workspace);
  if (!ok) return [false, msg];

  // --- Validate partial cubes ---
  [ok, msg] = validateCubes(workspace.partialSpectralCubes, "Spectral", true, workspace);
  if (!ok) return [false, msg];
  [ok, msg] = validateCubes(workspace.partialElementalCubes, "Elemental", true, workspace);
  if (!ok) return [false, msg];

  // --- Unique names check ---
  const names: string[] = [
    workspace.baseImage.name,
    ...workspace.contextualImages.map((img) => img.name),
    ...workspace.spectralCubes.map((c) => c.name),
    ...workspace.elementalCubes.map((c) => c.name),
    ...workspace.partialSpectralCubes.map((c) => c.name),
    ...workspace.partialElementalCubes.map((c) => c.name),
  ];
  if (new Set(names).size !== names.length) return [false, "Names must be unique"];

  return [true, ""];
}

/**
 * Helper function to validate base workspace properties.
 * @param workspace - The workspace to validate.
 * @returns - A boolean indicating if the workspace is correct and a possible error message.
 */
function validateWorkspaceHelper(workspace: WorkspaceConfig): [boolean, string] {
  // --- Base image ---
  if (workspace.baseImage.name.trim() === "") return [false, "Base image must have a name"];
  if (workspace.baseImage.imageLocation.trim() === "") return [false, "Base image must have an associated image file"];

  // --- Contextual images ---
  for (const image of workspace.contextualImages) {
    if (image.name.trim() === "") return [false, "Contextual image must have a name"];
    if (image.imageLocation.trim() === "") return [false, "Contextual image must have an associated image file"];
  }

  return [true, ""];
}

/**
 * Helper function to validate cubes.
 * @param cubes - The cubes to validate.
 * @param type - The type of cubes ("Spectral" or "Elemental").
 * @param isPartial - Whether the cubes are partial.
 * @param workspace - Workspace the cubes belong to.
 * @returns A boolean indicating if the cubes are correct and a possible error message.
 */
function validateCubes(
  cubes: ElementalCube[] | SpectralCube[],
  type: "Spectral" | "Elemental",
  isPartial: boolean,
  workspace: WorkspaceConfig,
): [boolean, string] {
  for (const cube of cubes) {
    if (cube.name.trim() === "") return [false, `${type} cube must have a name`];

    if (type === "Spectral") {
      const [isValid, errorMessage] = validateSpectralCubes(cube as SpectralCube, isPartial, workspace);
      if (!isValid) return [false, errorMessage];
    } else if (type === "Elemental") {
      const [isValid, errorMessage] = validateElementalCubes(cube as ElementalCube, isPartial, workspace);
      if (!isValid) return [false, errorMessage];
    }
  }
  return [true, ""];
}

/**
 * Helper function to validate a spectral cube.
 * @param cube - The spectral cube to validate.
 * @param isPartial - Whether the cube is partial.
 * @param workspace - The workspace configuration.
 * @returns A boolean indicating if the cube is correct and a possible error message.
 */
function validateSpectralCubes(cube: SpectralCube, isPartial: boolean, workspace: WorkspaceConfig): [boolean, string] {
  if (cube.rawLocation.trim() === "") return [false, "Spectral cube must have an associated raw file"];
  if (cube.rplLocation.trim() === "") return [false, "Spectral cube must have an associated rpl file"];
  if (!isPartial && workspace.stitchingMode === "full" && cube.recipeLocation.trim() === "") {
    return [false, "Spectral cube must have an associated recipe file"];
  }
  return [true, ""];
}

/**
 * Helper function to validate an elemental cube.
 * @param cube - The elemental cube to validate.
 * @param isPartial - Whether the cube is partial.
 * @param workspace - The workspace configuration.
 * @returns A boolean indicating if the cube is correct and a possible error message.
 */
function validateElementalCubes(
  cube: ElementalCube,
  isPartial: boolean,
  workspace: WorkspaceConfig,
): [boolean, string] {
  if (cube.dataLocation.trim() === "") return [false, "Elemental cube must have an associated data file"];
  if (
    !isPartial &&
    workspace.stitchingMode === "full" &&
    workspace.spectralCubes.length === 0 &&
    cube.recipeLocation.trim() === ""
  ) {
    return [false, "Elemental cube must have an associated recipe file"];
  }
  return [true, ""];
}

/**
 * Initializes the elements in the workspace based on the elemental cubes.
 * @param workspace - The workspace to initialize.
 * @returns Whether the initialization was successful.
 */
export async function initializeChannels(workspace: WorkspaceConfig): Promise<boolean> {
  const response = await fetch(`${config.api.endpoint}/${workspace.name}/data/elements/names`);

  if (!response.ok) {
    return false;
  }

  const channelNames = (await response.json()) as string[];

  // Initialize the elemental channels array in the workspace
  workspace.elementalChannels = [];
  channelNames.forEach((channel, index) => {
    // Create an elemental channel object with channel index, name, and initial enabled state
    workspace.elementalChannels.push({
      channel: index,
      name: channel,
      enabled: false,
    });
  });

  return true;
}
