#!/usr/bin/env python

try:
    import setuptools
    from setuptools import setup
except ImportError:
    setuptools = None
    from distutils.core import setup


readme_file = 'README.md'
try:
    import pypandoc
    long_description = pypandoc.convert(readme_file, 'rst')
except (ImportError, OSError) as e:
    print('No pypandoc or pandoc: %s' % (e,))
    with open(readme_file) as fh:
        long_description = fh.read()

with open('./hn/version.py') as fh:
    for line in fh:
        if line.startswith('VERSION'):
            version = line.split('=')[1].strip().strip("'")

setup(
    name='hn',
    version=version,
    packages=['hn'],
    author='Tony Walkr',
    author_email='walkr.walkr@gmail.com',
    url='https://github.com/walkr/hn',
    license='MIT',
    description='',
    long_description=long_description,
    install_requires=[
        'oi',
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],

    entry_points={
        'console_scripts': [
            'hnd = hn.hnd:main',
            'hnctl = hn.hnctl:main',
        ],
    },

)
