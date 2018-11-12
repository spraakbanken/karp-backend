
from distutils.core import setup

setup(name='karp',
      version='0.2',
      description='',
      author='Språkbanken',
      author_email='sb-info@svenska.gu.se',
      url='https://spraakbanken.gu.se',
      packages=['karp'],
      entry_points={
          'console_scripts': [
              'karp-cli=karp.cli:app.cli'
          ]
      })
