# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = u"eNMS"
copyright = u"eNMS Automation"

# The short X.Y version.
version = "3.17.2"

# The full version, including alpha/beta/rc tags.
release = "3.17.2"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# A list of ignored prefixes for module index sorting.
modindex_common_prefix = []

html_theme_options = {"navigation_depth": 4}

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"  # winner, mobile friendly

# The style sheet to use for HTML pages. A file of that name must exist either
# in Sphinx’ static/ path, or in one of the custom paths given in
# html_static_path. Default is the stylesheet given by the selected theme.
html_style = "custom.css"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
