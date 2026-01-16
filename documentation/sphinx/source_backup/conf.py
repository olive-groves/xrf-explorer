# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys

from os.path import abspath, join

sys.path.insert(0, abspath(join("..", "..", "..")))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'XRF-Explorer 3.0'
author = ('Lonneke van Baren, Thijs van Berkel, Pijke van Bohemen, Stan van den Boogaart, Giovanni de Keijzer, Meie Koning, '
            'Daniël Koopmans, Marijn Kouwenberg, Jarno Vlaar, Sepp Vlassak')
credit1 = ('XRF-Explorer 2.0 by Pablo Benayas Penas, Jan Bulthuis, Dirk Burgers, Ivan Ivanov, Lotte Lakeman, Massimo Leal Martel, '
          'Sonia Maxim, Diego Rivera Garrido, Ruben Savelkouls, Iliyan Teofilov, Adrien Verriéle')
credit2 = ('Prototype concept by Dominique van Berkum')
copyright = (f'2024, Van Gogh Museum · Created by {author} · {credit1} · {credit2}')
release = '0.3.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.todo',  # allows TO-DO lists
              'sphinx.ext.viewcode',  # shows source code in the documentation
              'sphinx.ext.autodoc',  # automatically generate API documentation
              'sphinx.ext.githubpages',  # generates GitHub pages
              'sphinx.ext.imgmath',  # allows rendering math via LaTeX
              'sphinx.ext.duration',  # measures time to build Sphinx documentation
              'sphinx.ext.coverage',  # measures code coverage
              ]

templates_path = ['_templates']
exclude_patterns = []
add_module_names = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
