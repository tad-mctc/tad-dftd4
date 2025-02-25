# This file is part of tad-dftd4.
#
# SPDX-Identifier: Apache-2.0
# Copyright (C) 2024 Grimme Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Config file for docs.
"""
import os.path as op
import sys

sys.path.insert(0, op.join(op.dirname(__file__), "..", "src"))

import tad_dftd4

project = "Torch autodiff DFT-D4"
author = "Marvin Friede"
copyright = f"2022 {author}"

extensions = [
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

html_theme = "sphinx_book_theme"
html_title = project
html_logo = "_static/tad-dftd4.svg"
html_favicon = "_static/tad-dftd4-favicon.svg"

html_theme_options = {
    "repository_url": "https://github.com/dftd4/tad-dftd4",
    "repository_branch": "main",
    "use_repository_button": True,
    "use_edit_page_button": True,
    "use_download_button": False,
    "path_to_docs": "doc",
    "show_navbar_depth": 3,
    "logo_only": False,
}

html_sidebars = {}  # type: ignore[var-annotated]

html_css_files = [
    "css/custom.css",
]
html_static_path = ["_static"]
templates_path = ["_templates"]

autosummary_generate = True
autosummary_imported_members = True

autodoc_typehints = "description"
autodoc_member_order = "groupwise"
autoclass_content = "both"

intersphinx_mapping = {
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "python": ("https://docs.python.org/3", None),
    "tad_dftd3": ("https://tad-dftd3.readthedocs.io/en/latest/", None),
    "tad_mctc": ("https://tad-mctc.readthedocs.io/en/latest/", None),
    "tad_multicharge": (
        "https://tad-multicharge.readthedocs.io/en/latest/",
        None,
    ),
    "torch": ("https://pytorch.org/docs/stable/", None),
}

# Configuration for sphinx-copybutton
copybutton_prompt_text = ">>> |... "
copybutton_prompt_is_regexp = True

napoleon_google_docstring = False
napoleon_use_param = False
napoleon_use_ivar = True
napoleon_use_rtype = True

# The main toctree document.
main_doc = "index"
master_doc = "index"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    # Sometimes sphinx reads its own outputs as inputs!
    "build/html",
    "_build/html",
    "build/jupyter_execute",
    "_build/jupyter_execute",
    "notebooks/README.md",
    "README.md",
    "notebooks/*.md",
]
