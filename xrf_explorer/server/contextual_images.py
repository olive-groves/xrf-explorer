import os
import shutil
from xrf_explorer.server.file_system.config_handler import load_yml

allowed_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}


def set_contextual_image(path_to_image: str):
    """
    Saves a copy of the input file to contextual image folder.
    Allowed file types are ".png", ".jpg", ".jpeg", ".bmp", ".tiff" and ".tif".
    :param path_to_image: The path to the image that needs to be copied.
    """
    # Find the folder where the contextual image is stored.
    backend_config: dict = load_yml("config/backend.yml")
    if not backend_config:
        return ""
    folder = backend_config["contextual-images-folder"]

    # Check if the input file actually exists.
    if not os.path.isfile(path_to_image):
        raise FileNotFoundError(f"The file at path {path_to_image} does not exist.")

    # Check if the file extension is valid. If not, return.
    file_extension = path_to_image.split('.')[-1].lower()
    if file_extension not in allowed_formats:
        print(f"Unsupported file format: {file_extension}")
        return

    # Construct the destination path.
    destination_path = os.path.join(folder, f"contextual_image.{file_extension}")

    # Copy the image to the destination path
    shutil.copy(path_to_image, destination_path)


def get_contextual_image(file_type: str):
    # Find the folder where the contextual image is stored.
    backend_config: dict = load_yml("config/backend.yml")
    if not backend_config:
        return ""
    folder = backend_config["contextual-images-folder"]

    # Convert file type to lower case and ensure it starts with a period.
    file_extension = f".{file_type.lower()}" if not file_type.startswith('.') else file_type.lower()

    # Check if the file type is in an allowed format.
    if file_extension not in allowed_formats:
        print("Unsupported file format.")
        return None

    # Construct the file path.
    file_path = os.path.join(folder, f"contextual_image{file_extension}")

    # Check if the file exists and if so, return it.
    if os.path.isfile(file_path):
        return file_path
    else:
        return None
