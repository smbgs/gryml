#!/usr/bin/env bash

TITLE="Provisioning Gryml to pip test"
PYBASE="/venv/remak8s/bin/"

echo "$TITLE..."


$PYBASE/pip install --upgrade setuptools wheel twine

cd /remak8s/gryml/src/ || return

$PYBASE/python setup.py sdist bdist_wheel

$PYBASE/python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

echo "$TITLE done."