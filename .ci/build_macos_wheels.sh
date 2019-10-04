#!/usr/bin/env bash

set -e

brew update
brew outdated pyenv || brew upgrade pyenv
export PATH=~/.pyenv/shims:$PATH
for PYVER in "3.6.3" "3.7.0"; do
  pyenv install ${PYVER}
  pyenv global ${PYVER}
  pip install wheel
  python setup.py bdist_wheel
done
