import os
import sys

if os.path.abspath('..') in sys.path:
    pass
else:
    sys.path.append(os.path.abspath('..'))
from GeoAnalyze import __version__

# -- Project information -----------------------------------------------------

project = 'GeoAnalyze'
copyright = '2024, Debasish Pal'
author = 'Debasish Pal'
release = __version__

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode'
]

templates_path = [
    '_templates'
]

exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    '.ipynb_checkpoints'
]

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'

html_static_path = [
    '_static'
]

html_theme_options = {
    'prev_next_buttons_location': 'both'
}
