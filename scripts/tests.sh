#!/usr/bin/env bash

TITLE="Testing gryml local source version"
PYBASE="/venv/gryml/bin"

echo "$TITLE..."

cd /remak8s/gryml/tests/ || return 1
PYTHONPATH=/remak8s/gryml/src/ $PYBASE/python -m unittest discover -p "*_test.py"

echo "$TITLE done."