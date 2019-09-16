#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from setuptools import find_packages
from setuptools import setup


setup(
    name='karp',
    version='0.6.4',
    license='MIT License',
    description='',
    author='Språkbanken',
    author_email='sb-info@svenska.gu.se',
    url='https://spraakbanken.gu.se',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={'karp': [
        'schema/resourceconf.schema.json',
        'auth/pubkey.pem'
    ]},
    entry_points={
        'console_scripts': [
            'karp-cli=karp.cli:cli'
        ]
    },
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-cors',
        'click',
        'slacker-log-handler',
        'fastjsonschema',
    ],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 2 - Pre-Alpha',
        # 'Development Status ::  - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Utilities',
    ],
)
