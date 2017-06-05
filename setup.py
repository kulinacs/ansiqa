# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ansiqa',
    version='0.2.0',

    description='Anisible Role Quality Assurance',
    long_description=long_description,

    url='https://github.com/kulinacs/ansiqa',

    author='kulinacs',
    author_email='nicklaus@kulinacs.com',

    license='ISC',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='ansible automation documentation',

    packages=find_packages(),

    install_requires=['ruamel.yaml<0.15', 'argparse', 'tabulate', 'termcolor', 'jinja2', 'pygraphviz'],

    entry_points={
        'console_scripts': [
            'ansiqa=ansiqa:main',
        ],
    },
)
