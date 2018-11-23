#!/usr/bin/env python

import io
import os
import sys
from codecs import open
from shutil import rmtree

from setuptools import setup, Command

here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()


class PublishCommand(Command):
    """Support setup.py publish."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds...')
            rmtree(os.path.join(here, 'dist'))
        except FileNotFoundError:
            pass

        self.status('Building Source and Wheel (universal) distribution...')
        os.system('{} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine...')
        os.system('twine upload dist/*')

        sys.exit()

requires = ['SQLAlchemy;python_version>="3.0"',
            'pandas']
version = '0.1.0'


def read(f):
    return open(f, encoding='utf-8').read()

setup(
    name='pydbtools',
    version=version,
    description='Python package for querying and connecting to databases.',
    long_description=read('README.md') + '\n\n' + read('HISTORY.md'),
    author='Matthaeus Deutsch',
    author_email='matthaeus.deutsch@inwt-statistics.de',
    url='https://github.com/INWT/pydbtools',
    py_modules=['pydbtools'],
    package_data={'': ['LICENSE'],
                  'pydbtools': ['sql/*', 'tests/*']},
    install_requires=requires,
    extras_require={
        'pg': ['psycopg2'],
        'redshift': ['sqlalchemy-redshift', 'psycopg2'],
        'mysql': ['pymysql']
    },
    license='ISC',
    zip_safe=False,
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
    cmdclass={
        'publish': PublishCommand,
    }
)
