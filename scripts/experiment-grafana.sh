#!/usr/bin/env bash

TITLE="Testing gryml experiment : Grafana chart"
PYBASE="/venv/gryml/bin"

echo "$TITLE..."

PYTHONPATH=/remak8s/gryml/src/ $PYBASE/python /remak8s/gryml/src/gryml/cli.py -f /remak8s/gryml/experiments/grafana-gryml/values.yaml

echo "$TITLE done."