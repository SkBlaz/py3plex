#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Practical Multilayer Network Analysis with Py3plex - Book Configuration
#

import os
import sys

# Add py3plex to path
sys.path.insert(0, os.path.abspath('../py3plex'))

# -- Project information -----------------------------------------------------

project = 'Practical Multilayer Network Analysis with Py3plex'
copyright = '2025, Blaž Škrlj'
author = 'Blaž Škrlj'

# The version info for the project
version = '1.0.2'
release = '1.0.2'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

language = 'en'

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

pygments_style = 'sphinx'

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "navigation_depth": 4,
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "both",
    "style_external_links": False,
    "collapse_navigation": False,
    "sticky_navigation": True,
}

html_title = "Practical Multilayer Network Analysis with Py3plex"

# Add custom static files
html_static_path = ['_static']

# Add custom CSS files
html_css_files = [
    'custom.css',
]

# -- Options for LaTeX/PDF output --------------------------------------------

latex_engine = 'pdflatex'

latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': r'''
        \usepackage{amsmath}
        \usepackage{amssymb}
    ''',
    'figure_align': 'htbp',
    # Set proper table of contents depth for PDF
    'extraclassoptions': 'openany,oneside',
    # Prevent "(continues on next page)" markers in code blocks and tables
    'sphinxsetup': 'verbatimhintsturnover=false',
}

latex_documents = [
    (master_doc, 'py3plex_book.tex', 
     'Practical Multilayer Network Analysis with Py3plex',
     'Blaž Škrlj', 'manual'),
]

# Use chapter-level sectioning for PDF (makes ToC show chapters properly)
latex_toplevel_sectioning = 'chapter'

# Set ToC depth for better PDF navigation
latex_domain_indices = True
latex_show_pagerefs = True
latex_show_urls = 'footnote'

# -- Options for manual page output ------------------------------------------

man_pages = [
    (master_doc, 'py3plex_book', 
     'Practical Multilayer Network Analysis with Py3plex',
     [author], 1)
]

# -- Options for Epub output -------------------------------------------------

epub_title = project
epub_exclude_files = ['search.html']

# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'networkx': ('https://networkx.org/documentation/stable/', None),
}

# Math support
mathjax_path = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
