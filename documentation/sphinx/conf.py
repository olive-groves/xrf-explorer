# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'XRF-Explorer'
copyright = '2024, Pablo Benayas Penas, Jan Bulthuis, Dirk Burgers, Ivan Ivanov, Lotte Lakeman, Massimo Leal Martel, Sonia Maxim, Diego Rivera Garrido, Ruben Savelkouls, Iliyan Teofilov, Adrien Verriéle'
author = 'Pablo Benayas Penas, Jan Bulthuis, Dirk Burgers, Ivan Ivanov, Lotte Lakeman, Massimo Leal Martel, Sonia Maxim, Diego Rivera Garrido, Ruben Savelkouls, Iliyan Teofilov, Adrien Verriéle'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
