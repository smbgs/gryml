#!/usr/bin/env bash

TITLE="Provisioning Gryml to pip"

echo "$TITLE..."

pip install --upgrade setuptools wheel twine

cd ./gryml/src/ || return

python setup.py sdist bdist_wheel

python -m twine upload dist/*

rm -rf build
rm -rf dist
rm -rf gryml.egg-info

echo "$TITLE done."