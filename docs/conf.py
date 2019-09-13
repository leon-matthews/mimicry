
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = u'Mimicry'
copyright = u'2012-2019 Leon Matthews'

version = '0.1'

release = '0.1'

exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_theme = 'default'

html_static_path = ['_static']

htmlhelp_basename = 'Mimicrydoc'

latex_elements = {}

latex_documents = [
  ('index', 'Mimicry.tex', u'Mimicry Documentation',
   u'Leon Matthews', 'manual'),
]

man_pages = [
    ('index', 'mimicry', u'Mimicry Documentation',
     [u'Leon Matthews'], 1)
]

texinfo_documents = [
  ('index', 'Mimicry', u'Mimicry Documentation',
   'Leon Matthews', 'Mimicry', 'One line description of project.',
   'Miscellaneous'),
]

epub_title = 'Mimicry'
epub_author = 'Leon Matthews'
epub_publisher = 'Leon Matthews'
epub_copyright = copyright
