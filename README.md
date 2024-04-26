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

The frontend is stored in the `xrf_explorer/client` directory. The frontend is based on Vue. For developing the frontend Node.js is required.

`npm run dev` starts a development server and `npm run build` compiles the website to the `xrf_explorer/client/dist` directory from which it can be served by the Flask backend.

UI components are taken from the [shadcn-vue](https://www.shadcn-vue.com) project, documentation for which can be found [here](https://www.shadcn-vue.com/docs).
