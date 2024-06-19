# XRF-Explorer

Repository for the XRF Explorer team.

## Development information

### Backend

The XRF-Explorer backend is a Flask app served by waitress. The `xrf_explorer/__init__.py` file contains the setup for
the backend app and the `run.py` file is the main file from which the backend is run. Further backend code is located in
the `xrf_explorer/server` directory.

#### Dependencies

##### Python

The project's backend runs on [Python 3.12](https://docs.python.org/3/whatsnew/3.12.html). To get started, download and
install python from one of the following sources (depending on your OS):

- Install on [Windows](https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe)
- Install on Linux (Ubuntu):

  ```bash
  sudo apt-get update && sudo apt-get upgrade -y
  sudo apt-get install python3.12
  ```

##### Python Libraries

Once you have the correct Python version installed, we highly recommend creating a virtual environment for the project,
in order to keep dependencies containerized and the `requirements.txt` file as limited as possible.

All dependencies needed to run and contribute to the project are located in the `requirements.txt` file in the root
directory. To install the dependencies, simply run:

`pip install -r requirements.txt`

The file can easily be updated by running `pip freeze > requirements.txt`.
WARNING: this command will place all the dependencies you have currently installed in the `requirements.txt` file, so
make sure you have removed any unnecessary dependencies from your environment beforehand.

##### Tools

To automatically generate the code's documentation we use [sphinx](https://www.sphinx-doc.org/en/master/). In order to
use sphinx and build the documentation, you will need Make.
If you're using Linux, this should already be pre-installed.
If you're using Windows, you can install Make with the Chocolatey package manager, which is installed
alongside [Node.js](#dependencies-1). Once you have Chocolatey installed, simply run `choco install make` from the CMD
or PowerShell.

##### Environment Variables

During development, we want the backend to log to the console, but in production, we want the server to logs to be sent
to a log file. For this reason, you can set up the following environment variable:

- `XRF_EXPLORER_LOG_MODE`: when set to "PROD", it will output the logs to a log file instead of the console
  Note that if the environment variable is not set, the logging will be sent to standard output.

#### Development Process

To start the backend, you can simply run `python run.py` from the root directory.

If you would like to test communication with a remote server, we recommend installing a VM running Ubuntu 23.04 and
changing the necessary fields in `config/backend.yml`.

#### Generating Documentation

Generating the code documentation is very simple and only requires a couple of steps:

- Navigate to the project's root folder
- From the terminal run `sphinx-apidoc(.exe) -f -o ./documentation/sphinx/source/ .` to generate the ReST files. _The
  .exe extension may be omitted in some environments._
- Build the documentation in HTML format with `./documentation/sphinx/make html` (run `./documentation/sphinx/make` to
  see all available formats)

### Frontend

The frontend is stored in the `xrf_explorer/client` directory. The frontend is based on Vue.js and UI components are
taken from the [shadcn-vue](https://www.shadcn-vue.com) project, documentation for which can be
found [here](https://www.shadcn-vue.com/docs).

#### Dependencies

For developing the frontend `npm` is required. To avoid issues, we recommend
installing [Node.js v20](https://nodejs.org/en/download), which comes with `npm` packaged:

- Install on [Windows](https://nodejs.org/dist/v20.12.2/node-v20.12.2-x64.msi).

- Install on Linux (Ubuntu):

    ```bash
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y curl
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    ```

- (Optional) You can alternatively easily manage multiple Node and npm versions directly from the CLI
  using [Node Version Manager](https://github.com/coreybutler/nvm-windows#readme).

You can check that you have the correct versions with `node --version` and `npm --version` (The npm version you should
be using is specified in `xrf_explorer/client/package.json`)

#### Development Process

To get started with the development process, run:

- `npm install` to download and install all the dependencies specified in `xrf_explorer/client/package.json`
- `cd xrf_explorer/client` to move to the frontend development directory
- `npm run build` compiles the website to the `xrf_explorer/client/dist` directory from which it can be served by the
  Flask backend.
- `npm run dev` starts a development server

To enforce consistency in the client code, `prettier` and `eslint` have been configured to check code style.

- `npm run style:check` Checks if the client code conforms to the prettier and eslint rules.
- `npm run style:fix` is able to fix some of the errors reported by `style:check`.
- Setting up the [prettier](https://prettier.io/) formatter to automatically format on save can immediately remove large
  amounts of errors.

### Workspace structure

All data used by XRF-Explorer is located in the `uploads-folder` as defined by the configuration
file (`backend/config.yml` by default). In this directory every subdirectory is a separate workspace (a set of data
files for a single painting).

- `uploads-folder\<painting>\` - The directory containing data for the painting `<painting>`.
- `uploads-folder\<painting>\workspace.json` - A file containing descriptive information describing all information
  present for the painting. Must be present for XRF-Explorer to be able to load the painting.
- `uploads-folder\<painting>\<filename>` - Any other file containing data related to `<painting>`. For all functionality
  to work there should be at least a base image file, `.csv` files containing the registering information for all data
  except the base image file, a `.dms` or `.csv` file containing an elemental datacube and a `.raw` and `.rpl` file
  containing raw spectral data. The names of all these files must be specified in `workspace.json` for XRF-Explorer to
  recognize them.

#### `workspace.json` format

The `workspace.json` file follows the following format:

```json5
{
  // Must be exactly equal to the name of the directory
  "name": "<painting>",
  // The base image that everything will be registered to
  "baseImage": {
    "name": "<name>",
    // The filename of the base image file
    "imageLocation": "<filename>",
    // The filename of the registering recipe for the image
    // The base image should not be registered
    "recipeLocation": ""
  },
  // Array of additional contextual images
  // Every contextual image follows the same format as baseImage
  "contextualImages": [],
  // Array of spectral data cubes
  // Only a single cube per workspace is currently supported
  "spectralCubes": [
    {
      // Name must be unique
      "name": "<name>",
      // The filename of the raw file
      "rawLocation": "<filename>",
      // The filename of the rpl file
      "rplLocation": "<filename>",
      // The filename of the registering recipe for the data cube
      "recipeLocation": "<filename>"
    }
  ],
  // Array of elemental data cubes
  // Only a single cube per workspace is currently supported
  // Every elemental datacube must have the same channels
  "elementalCubes": [
    {
      // Name must be unique
      "name": "<name>",
      // Must be 'csv' or 'dms'
      "fileType": "<filetype>",
      // Filename of the data cube
      "dataLocation": "<filename>",
      // The filename of the registering recipe for the data cube
      "recipeLocation": "<filename>"
    }
  ],
  // Array of elemental channels
  "elementalChannels": [
    {
      // Name of the elemental channel
      "name": "<name>",
      // The index of the channel in the elemental cubes
      "channel": 0,
      // Whether the channel is enabled
      // Disabled channels will not be visible in the client
      "enabled": false,
    }
  ]
}
```

Take into account that filenames must include the extension type (i.e. `spectral.raw` instead of just `spectral`).
