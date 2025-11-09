import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))
sys.path.insert(0, os.path.abspath('../../'))

project = 'Memory Scramble Game'
copyright = '2025, Daria Rateeva'
author = 'Daria Rateeva'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Use furo theme instead of alabaster
html_theme = 'furo'
html_static_path = ['_static']

autodoc_member_order = 'bysource'
autoclass_content = 'both'

# Furo theme options
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#1e90ff",
        "color-brand-content": "#ff6b6b",
    },
}
