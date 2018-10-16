# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 00:29:55 2015

Setup file for the pysigview_cs module.

Ing.,Mgr. (MSc.) Jan Cimbálník
Biomedical engineering
International Clinical Research Center
St. Anne's University Hospital in Brno
Czech Republic
&
Mayo systems electrophysiology lab
Mayo Clinic
200 1st St SW
Rochester, MN
United States
"""

# Std library imports
import os
import os.path as osp
from setuptools import setup

# Third party imports

# Local imports


# =============================================================================
# Constants
# =============================================================================
NAME = 'pysigview_cs'
LIBNAME = 'pysigview_cs'

# =============================================================================
# Auxiliary functions
# =============================================================================


def get_subpackages(name):
    """Return subpackages of package *name*"""
    splist = []
    for dirpath, _dirnames, _filenames in os.walk(name):
        if osp.isfile(osp.join(dirpath, '__init__.py')):
            splist.append(".".join(dirpath.split(os.sep)))
    return splist


def get_packages():
    """Return package list"""
    packages = (
        get_subpackages(LIBNAME)
        )
    return packages

# =============================================================================
# Setup arguments
# =============================================================================


setup_args = dict(name='pysigview_cs',
                  version='0.1.2',
                  description='Pysigview client-server',
                  url='https://github.com/ICRC-BME/PySigView_cs',
                  author='Jan Cimbalnik',
                  author_email='jan.cimbalnik@fnusa.cz',
                  license='Apache 2.0',
                  packages=get_packages(),
                  platforms=['Linux', 'MacOS'],
                  keywords='client server pysigview signals',
                  install_requires=['numpy', 'pyzmq', 'pymef>=0.2', 'pydread'],
                  zip_safe=False,
                  classifiers=['License :: OSI Approved :: MIT License',
                               'Operating System :: MacOS',
                               # 'Operating System :: Microsoft :: Windows',
                               'Operating System :: POSIX :: Linux',
                               'Programming Language :: Python :: 3',
                               'Development Status :: 5 - Production/Stable',
                               'Topic :: Scientific/Engineering'])

# =============================================================================
# Run setup
# =============================================================================


setup(**setup_args)
