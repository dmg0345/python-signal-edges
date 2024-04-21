"""Configuration file for the Sphinx documentation builder, relevant links for documentation of Sphinx are shown below:

    - https://www.sphinx-doc.org/en/master/usage/configuration.html
    - Conditional Documentation: https://stackoverflow.com/a/45637280/21951997
"""

# pylint: skip-file
# type: ignore

## Imports #############################################################################################################
import os
import sys


## Path setup ##########################################################################################################
def collect_folders(path: str) -> list[str]:
    """Traverses a folder and returns all the subfolders."""
    # Ensure folder exists and it is a directory.
    final_dirs = []
    if not os.path.exists(path) or not os.path.isdir(path):
        return final_dirs

    # Collect root directory and subfolders.
    final_dirs = [os.path.normpath(os.path.realpath(path))]
    for root, dirs, _ in os.walk(path):
        for name in dirs:
            if name not in ["__pycache__", ".pytest_cache"]:
                final_dirs.append(os.path.normpath(os.path.realpath(os.path.join(root, name))))

    return final_dirs


# If extensions (or modules to document with autodoc) are in another directory, add these directories to sys.path here.
root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path = [*collect_folders(os.path.join(root, "src")), *sys.path]
sys.path = [*collect_folders(os.path.join(root, "tests")), *sys.path]

## Project information #################################################################################################
# Project name.
project = "python-signal-edges"
# Friendly name.
friendly_name = "Signal Edges"
# Project author.
author = "Diego Martinez <dmg0345@gmail.com>"
# Project copyright.
copyright = author
# Project version.
version = "1.0.5"
# Project release, set it as the same value as version as the separation is not required.
release = version

## Sphinx General configuration ########################################################################################
# Sphinx and custom extensions.
extensions = [
    # Autodoc Extension:
    #    - https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
    "sphinx.ext.autodoc",
    # Autodoc Extension Type Variables:
    #    - https://sphinx-toolbox.readthedocs.io/en/latest/extensions/more_autodoc/typevars.html
    "sphinx_toolbox.more_autodoc.typevars",
    # Autodoc Extension Type Hints:
    #    - https://sphinx-toolbox.readthedocs.io/en/latest/extensions/more_autodoc/typehints.html
    #    - https://github.com/agronholm/sphinx-autodoc-typehints
    "sphinx_toolbox.more_autodoc.typehints",
    # Intersphinx Extension:
    #    - https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
    "sphinx.ext.intersphinx",
    # Todo Extension:
    #    - https://www.sphinx-doc.org/en/master/usage/extensions/todo.html
    "sphinx.ext.todo",
    # Read The Docs theme extension:
    #    - https://github.com/readthedocs/sphinx_rtd_theme
    #    - https://sphinx-rtd-theme.readthedocs.io/en/stable/
    "sphinx_rtd_theme",
]
# File extensions of source files.
source_suffix = {".rst": "restructuredtext"}
# Encoding of reST files.
source_encoding = "utf-8-sig"
# Root document.
root_doc = "index"
# Glob-style patterns to exclude when looking for source files.
exclude_patterns = [".sphinx_build"]
# Included at the end of every RestructuredText source file that is read.
rst_epilog = f""""""
# Included at the beginning of every RestructuredText source file that is read.
rst_prolog = f"""
.. |ProjectName| replace:: **{project}**
.. |ProjectFriendlyName| replace:: **{friendly_name}**
.. |ProjectCopyright| replace:: **{copyright}**
.. |ProjectVersion| replace:: **{version}**
"""
# Enable nitpicky mode.
nitpicky = True
# What to ignore from nitpicky mode.
nitpick_ignore = []
nitpick_ignore_regex = ((r"py:.*", r"numpy\..*"), (r"pya:.*", r"scipy\..*"), (r"pya:.*", r"matplotlib\..*"))
# Unset pygments style so that the one of the default theme is used for highlighting.
pygments_style = None
# Keep module names hidden in the documentation as that results in too verbose documentation.
add_module_names = False
# Do not add objects such as classes, functions or methods as part of the TOC.
toc_object_entries = False

## Sphinx Internalization configuration ################################################################################
# Set language to english.
language = "en"

## Sphinx HTML output configuration ####################################################################################
# The theme to use.
html_theme = "sphinx_rtd_theme"
# Specific options for the theme.
html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "style_external_links": False,
    "collapse_navigation": False,
    "includehidden": True,
    "navigation_depth": 2,
}
# HTML title.
html_title = f"{friendly_name} v{version}"
# HTML short title.
html_short_title = html_title
# HTML base URL which points to the root HTML documentation.
html_baseurl = ""
# Path to the HTML logo.
html_logo = ".assets/img/logo_128x128.png"
# Path to the HTML fav icon.
html_favicon = ".assets/img/logo_16x16.png"
# Add permalinks to every section.
html_permalinks = True
# Do not include the original sources in the final documentation.
html_copy_source = False
# Do not include links to the sources in the documentation.
html_show_sourcelink = False
# Show copyright in the HTML footer.
html_show_copyright = True
# Disable created by Sphinx text in the HTML footer.
html_show_sphinx = False
# Set the language for the search to english.
html_search_language = "en"

## AutoDoc Extension configuration #####################################################################################
# For classes, document the class docstring only for the main body.
autoclass_content = "class"
# Display signature for a class as a method.
autodoc_class_signature = "separated"
# Order members by order of appearance by source.
autodoc_member_order = "bysource"
# Flags to include in every directive.
autodoc_default_options = {
    # "members": "init",
    "member-order": "bysource",
    "undoc-members": "bysource",
    # "private-members": "",
    # "special-members": "",
    # "inherited-members": "",
    # "show-inheritance": "",
    # "ignore-module-all": "",
    # "imported-members": "",
    # "exclude-members": "",
    # "class-doc-from": "",
    # "no-value": "",
}
# Keep typehints in the signature of methods / functions.
autodoc_typehints = "signature"
# Keep typehints short as for them not to be excessively verbose.
autodoc_typehints_format = "short"
# Set Autodoc warnings to errors.
autodoc_warningiserror = True
# Inherit docstrings from parents if they are not explicitly set.
autodoc_inherit_docstrings = True

## AutoDoc Typevars Extension configuration ############################################################################
# Document all type variables.
all_typevars = True

## AutoDoc Typehints Extension configuration ###########################################################################
# Adds defaults to the documentation.
typehints_defaults = "braces"
# Do not use fully qualified names for type hints as otherwise it becomes too verbose.
typehints_fully_qualified = False
# Hides return types which are None.
hide_none_rtype = True
# Simplify optional unions.
simplify_optional_unions = True

## Intersphinx Extension configuration #################################################################################
# Locations and names to other projects to be linked to this documentation.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("http://docs.scipy.org/doc/numpy", None),
    "scipy": ("http://docs.scipy.org/doc/scipy/reference", None),
    "matplotlib": ("http://matplotlib.org/stable", None),
}

## ToDo Extension configuration ########################################################################################
# Do not emit warnings for todo directives.
todo_emit_warnings = True
