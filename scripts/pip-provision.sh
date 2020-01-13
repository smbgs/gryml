#!/usr/bin/env bash

TITLE="Provisioning Gryml to pip"
PYBASE="/venv/remak8s/bin/"

echo "$TITLE..."


$PYBASE/pip install --upgrade setuptools wheel twine

cd /remak8s/gryml/src/ || return

$PYBASE/python setup.py sdist bdist_wheel

$PYBASE/python -m twine upload --repository-url https://pypi.org/legacy/ dist/*

rm -rf build
rm -rf dist
rm -rf gryml.egg-info

echo "$TITLE done."