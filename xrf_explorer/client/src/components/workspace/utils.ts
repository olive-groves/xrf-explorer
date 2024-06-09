import { WorkspaceConfig } from "@/lib/workspace";
import { config } from "@/main";

/**
 * Validates a workspace to test if it is sufficient.
 * @param workspace - The workspace to validate.
 * @returns A boolean indicating if the workspace is correct and a possible error message.
 */
export function validateWorkspace(workspace: WorkspaceConfig): [boolean, string] {
  // Check if the base image has a name and associated image file
  if (workspace.baseImage.name.trim() == "") return [false, "Base image must have a name"];
  if (workspace.baseImage.imageLocation.trim() == "") return [false, "Base image must have an associated image file"];

  // Check if the contextual images have names and associated image files, and are valid
  for (const image of workspace.contextualImages) {
    if (image.name.trim() == "") return [false, "Contextual image must have a name"];
    if (image.imageLocation.trim() == "") return [false, "Contextual image must have an associated image file"];
  }

  // Check if the spectral cubes have names and associated files, and are valid
  if (workspace.spectralCubes.length == 0) return [false, "A spectral cube is required"];
  if (workspace.spectralCubes.length > 1) return [false, "Having multiple spectral cubes is currently not supported"];
  for (const cube of workspace.spectralCubes) {
    if (cube.name.trim() == "") return [false, "Spectral cube must have a name"];
    if (cube.rawLocation.trim() == "") return [false, "Spectral cube must have an associatiated raw file"];
    if (cube.rplLocation.trim() == "") return [false, "Spectral cube must have an associatiated rpl file"];
    if (cube.recipeLocation.trim() == "") return [false, "Spectral cube must have an associatiated recipe file"];
  }

  // Check if the elemental cubes have names and associated files, and are valid
  if (workspace.elementalCubes.length == 0) return [false, "An elemental cube is required"];
  if (workspace.elementalCubes.length > 1) return [false, "Having multiple elemental cubes is currently not supported"];
  for (const cube of workspace.elementalCubes) {
    if (cube.name.trim() == "") return [false, "Elemental cube must have a name"];
    if (cube.dataLocation.trim() == "") return [false, "Elemental cube must have an associatiated data file"];
    if (cube.recipeLocation.trim() == "") return [false, "Elemental cube must have an associatiated recipe file"];
  }

  // Check if the elemental channels have names and are unique
  const names = [];
  names.push(workspace.baseImage.name);
  workspace.contextualImages.forEach((image) => names.push(image.name));
  workspace.spectralCubes.forEach((cube) => names.push(cube.name));
  workspace.elementalCubes.forEach((cube) => names.push(cube.name));
  if (new Set(names).size !== names.length) return [false, "Names must be unique"];

  return [true, ""];
}

/**
 * Initializes the elements in the workspace based on the elemental cubes.
 * @param workspace - The workspace to initialize.
 * @returns Whether the initialization was successfull.
 */
export async function initializeChannels(workspace: WorkspaceConfig): Promise<boolean> {
  const response = await fetch(`${config.api.endpoint}/${workspace.name}/element_names`);

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
