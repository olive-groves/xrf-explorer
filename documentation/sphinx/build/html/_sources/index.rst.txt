.. XRF-Explorer documentation master file, created by
   sphinx-quickstart on Mon May 13 17:45:51 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

********************************************
Welcome to XRF-Explorer 2.0's documentation!
********************************************

The XRF Explorer 2.0 is a web application aimed at conservation scientists, that facilitates the analysis of paintings composition. Here you will find information about its source code, including how it works and how to use it for future development.

Getting Started
===============

In this section you will find all the necessary steps to be able to run and contribute to the XRF-Explorer 2.0 codebase.


Backend Configuration
---------------------

The XRF-Explorer backend is a Flask app served by waitress. The ``xrf_explorer/__init__.py`` file contains the setup for the backend app and the ``run.py`` file is the main file from which the backend is run. Further backend code is located in the ``xrf_explorer/server`` directory.

Backend Dependencies
^^^^^^^^^^^^^^^^^^^^

Python
++++++

The project's backend runs on `Python 3.12 <https://docs.python.org/3/whatsnew/3.12.html>`_. To get started, download and install python from one of the following sources (depending on your OS):

* Install on `Windows <https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe>`__
* Install on Linux (Ubuntu):

   $ sudo apt-get update && sudo apt-get upgrade -y

   $ sudo apt-get install python3.12

Python Libraries
++++++++++++++++

Once you have the correct Python version installed, we highly recommend creating a virtual environment for the project, in order to keep dependencies containerized and the ``requirements.txt`` file as limited as possible.

All dependencies needed to run and contribute to the project are located in the ``requirements.txt`` file in the root directory. To install the dependencies, simply run:

   $ pip install -r requirements.txt

The file can easily be updated by running

   $ pip freeze > requirements.txt

WARNING: this command will place all the dependencies you have currently installed in the ``requirements.txt`` file, so make sure you have removed any unnecessary dependencies from your environment beforehand.

Tools
+++++

To automatically generate the code's documentation we use `sphinx <https://www.sphinx-doc.org/en/master/>`_. In order to use sphinx and build the documentation, you will need Make.
If you're using Linux, this should already be pre-installed.
If you're using Windows, you can install Make with the Chocolatey package manager, which is installed alongside Node.js (see `Frontend Dependencies`_). Once you have Chocolatey installed, simply run ``choco install make`` from the CMD or PowerShell.

Running the Backend
^^^^^^^^^^^^^^^^^^^

To start the backend, you can simply run from the root directory:

   $ python run.py

If you would like to test communication with a remote server, we recommend installing a VM running Ubuntu 23.04 and changing the necessary fields in ``xrf_explorer/client/config.ts``.

Generating Documentation
^^^^^^^^^^^^^^^^^^^^^^^^

Generating the code documentation is very simple and only requires a couple of steps:

* Navigate to the project's root folder
* From the terminal run the following to generate the ReST files. *The .exe extension may be omitted in some environments.*

   $ sphinx-apidoc(.exe) -f -o ./documentation/sphinx/source/ .

* Build the documentation in HTML format with

   $ ./documentation/sphinx/make html

* You can see all available formats with

   $ ./documentation/sphinx/make

Frontend Configuration
----------------------

The frontend is stored in the ``xrf_explorer/client`` directory. The frontend is based on Vue.js and UI components are taken from the `shadcn-vue <https://www.shadcn-vue.com>`_ project, documentation for which can be found `here <https://www.shadcn-vue.com/docs>`_.

Frontend Dependencies
^^^^^^^^^^^^^^^^^^^^^

For developing the frontend ``npm`` is required. To avoid issues, we recommend installing `Node.js v20 <https://nodejs.org/en/download>`_, which comes with ``npm`` packaged:

* Install on `Windows <https://nodejs.org/dist/v20.12.2/node-v20.12.2-x64.msi>`__.
* Install on Linux (Ubuntu):

   $ sudo apt update

   $ sudo apt upgrade -y

   $ sudo apt install -y curl

   $ curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

   $ sudo apt install -y nodejs

* (Optional) You can alternatively easily manage multiple Node and npm versions directly from the CLI using `Node Version Manager <https://github.com/coreybutler/nvm-windows#readme>`_.

You can check that you have the correct versions with

   $ node --version

and

   $ npm --version

(The npm version you should be using is specified in ``xrf_explorer/client/package.json``)

Running the Frontend
^^^^^^^^^^^^^^^^^^^^

To get started with the development process, run:

* Download and install all the dependencies specified in ``xrf_explorer/client/package.json`` with:

   $ npm install

* Move to the frontend development directory:

   $ cd xrf_explorer/client

* Compile the website to the ``xrf_explorer/client/dist`` directory, from which it can be served by the Flask backend, by running:

   $ npm run build

* Start a development server with

   $ npm run dev

Frontend Codestyle
^^^^^^^^^^^^^^^^^^

To enforce consistency in the client code, ``prettier`` and ``eslint`` have been configured to the check code style.

* Check if the client code conforms to the ``prettier`` and ``eslint`` rules:

   $ npm run style:check

* Fix some of the errors reported by ``style:check``:

   $ npm run style:fix

* Setting up the `prettier <https://prettier.io/>`_ formatter to automatically format on save can immediately remove large amounts of errors.

Code Documentation
==================

.. toctree::
   :maxdepth: 3
   :caption: Python Modules:

   modules

.. toctree::
   :maxdepth: 3
   :caption: Vue Components:

   components

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
