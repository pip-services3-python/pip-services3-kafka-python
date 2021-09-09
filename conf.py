# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

# read the docs theme
import sphinx_rtd_theme

# -- Project information -----------------------------------------------------

project = 'pip-services3-kafka'
copyright = '2021, Sergey Seroukhov'
author = 'Sergey Seroukhov, Danil Prisiazhnyi'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

extensions = [
    'sphinx.ext.autodoc',
    # 'sphinx.ext.intersphinx',
    'sphinx.ext.githubpages',
    'sphinx_rtd_theme'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    'conf',
    'examples',
    'setup',
    'test',
]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Looks for objects in external projects
intersphinx_mapping = {'python': ('http://docs.python.org/2', None),
                       'scipy': ('http://docs.scipy.org/doc/scipy/reference/', None),
                       'pip_services3_commons': ('https://pip-services3-python.github.io/pip-services3-commons-python/index.html', None),
                       'pip_services3_components': ('https://pip-services3-python.github.io/pip-services3-components-python/index.html', None),
                        'pip_services3_rpc': ('https://pip-services3-python.github.io/pip-services3-rpc-python/index.html', None),
                        'pip_services3_messaging': ('https://pip-services3-python.github.io/pip-services3-messaging-python/index.html', None)}
