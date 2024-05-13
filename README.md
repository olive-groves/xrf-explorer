# XRF-Explorer

Repository for the XRF Explorer team.

## Development information

### Backend

The XRF-Explorer backend is a Flask app served by waitress. The `xrf_explorer/__init__.py` file contains the setup for the backend app and the `run.py` file is the main file from which the backend is run. Further backend code is located in the `xrf_explorer/server` directory.

#### Dependencies

##### Python

The project's backend runs on [Python 3.12](https://docs.python.org/3/whatsnew/3.12.html). To get started, download and install python from one of the following sources (depending on your OS):
- Install on [Windows](https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe)
- Install on Linux (Ubuntu): 
  ```bash
  sudo apt-get update && sudo apt-get upgrade -y
  sudo apt-get install python3.12
  ```

##### Python Libraries

Once you have the correct Python version installed, we highly recommend creating a virtual environment for the project, in order to keep dependencies containerized and the `requirements.txt` file as limited as possible.

All dependencies needed to run and contribute to the project are located in the `requirements.txt` file in the root directory. To install the dependencies, simply run:

`pip install -r requirements.txt`

The file can easily be updated by running `pip freeze > requirements.txt`.
WARNING: this command will place all the dependencies you have currently installed in the `requirements.txt` file, so make sure you have removed any unnecessary dependencies from your environment beforehand.

##### Tools

To automatically generate the code's documentation we use [sphinx](https://www.sphinx-doc.org/en/master/). In order to use sphinx and build the documentation, you will need Make.
If you're using Linux, this should already be pre-installed.
If you're using Windows, you can install Make with the Chocolatey package manager, which is installed alongside [Node.js](#dependencies-1). Once you have Chocolatey installed, simply run `choco install make` from the CMD or PowerShell.

#### Development Process

To start the backend, you can simply run `python run.py` from the root directory.

If you would like to test communication with a remote server, we recommend installing a VM running Ubuntu 23.04 and changing the necessary fields in `config/backend.yml`.

#### Generating Documentation

Generating the code documentation is very simple and only requires a couple of steps:
- Navigate to the project's root folder
- From the terminal run `sphinx-apidoc(.exe) -f -o .documentation/sphinx/source/ .` to generate the ReST files. _The .exe extension may be omitted in some environments._
- Build the documentation in HTML format with `documentation/sphinx/make html` (run `documentation/sphinx/make` to see all available formats)

### Frontend

The frontend is stored in the `xrf_explorer/client` directory. The frontend is based on Vue.js and UI components are taken from the [shadcn-vue](https://www.shadcn-vue.com) project, documentation for which can be found [here](https://www.shadcn-vue.com/docs).

#### Dependencies

For developing the frontend `npm` is required. To avoid issues, we recommend installing [Node.js v20](https://nodejs.org/en/download), which comes with `npm` packaged: 
- Install on [Windows](https://nodejs.org/dist/v20.12.2/node-v20.12.2-x64.msi).
- Install on Linux (Ubuntu):
    ```bash
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y curl
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    ```
- (Optional) You can alternatively easily manage multiple Node and npm versions directly from the CLI using [Node Version Manager](https://github.com/coreybutler/nvm-windows#readme).

You can check that you have the correct versions with `node --version` and `npm --version` (The npm version you should be using is specified in `xrf_explorer/client/package.json`)

#### Development Process

To get started with the development process, run:
- `npm install` to download and install all the dependencies specified in `xrf_explorer/client/package.json`
- `cd xrf_explorer/client` to move to the frontend development directory
- `npm run build` compiles the website to the `xrf_explorer/client/dist` directory from which it can be served by the Flask backend.
- `npm run dev` starts a development server
