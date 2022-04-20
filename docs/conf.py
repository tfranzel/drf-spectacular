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
import os
import sys

from django.conf import settings

settings.configure(USE_I18N=False, USE_L10N=False)

sys.path[:0] = [os.path.abspath('../'), os.path.abspath('./')]

# -- Project information -----------------------------------------------------

project = 'drf-spectacular'
copyright = '2020, T. Franzel'
author = 'T. Franzel'

needs_sphinx = '4.1'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'extensions',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

default_role = 'default-role-error'

linkcheck_allowed_redirects = {
    r"^https://tox\.wiki/$": r"https://tox\.wiki/en/latest/$",
    r"^https://drf-spectacular\.readthedocs\.io/$": r"https://drf-spectacular\.readthedocs\.io/en/latest/$",
    r"^https://docs\.djangoproject\.com/en/stable/": r"^https://docs\.djangoproject\.com/en/\d+\.\d+/",
    r"^https://github\.com/tfranzel/drf-spectacular/issues/\d+": "https://github\.com/tfranzel/drf-spectacular/pull/\d+",
}

linkcheck_ignore = [
    # Special-use addresses and domain names. (RFC 6761/6890)
    r"^https?://(?:127\.0\.0\.1|\[::1\])(?::\d+)?/",
    r"^https?://(?:[^/\.]+\.)*example\.(?:com|net|org)(?::\d+)?/",
    r"^https?://(?:[^/\.]+\.)*(?:example|invalid|localhost|test)(?::\d+)?/",
]

nitpicky = True

nitpick_ignore_regex = [
    # Unresolvable type hinting forward references.
    ('py:class', r'(?:APIView|AutoSchema|OpenApiFilterExtension)'),
    # Unresolvable type hinting references to packages without intersphinx support.
    ('py:class', r'rest_framework\..+'),
    # Internal undocumented objects.
    ('py:class', r'drf_spectacular\.generators\..+'),
    ('py:class', r'drf_spectacular\.plumbing\..+'),
    ('py:class', r'drf_spectacular\.utils\.F'),
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'django': ('https://docs.djangoproject.com/en/stable/', 'https://docs.djangoproject.com/en/stable/_objects/'),
    'drf-yasg': ('https://drf-yasg.readthedocs.io/en/stable/', None),
}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
