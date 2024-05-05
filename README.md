# XRF-Explorer

Repository for the XRF Explorer team.

## Installation

1. `conda env create --file requirements.yml --prefix ./env`

## Running server

1. `conda activate ./env`
2. `python run.py`

## Development information

### Backend

The XRF-Explorer backend is a Flask app served by waitress. The `xrf_explorer` folder contains `__init__.py` which contains the setup for the backend app, further code is split up between `xrf_explorer/server` and `xrf_explorer/client`.

The `client` folder contains the frontend project that will be served to the user as part of the Flask backend.

The `server` folder contains all python code necessary for the backend of the app.

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
