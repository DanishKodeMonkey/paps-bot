#!/usr/bin/env bash

CODE_PATH="paps_bot"

echo "Linting project with pylint ..."
echo "=================================================="

pylint "$CODE_PATH"

echo "=================================================="
echo "Done running pylint"
echo
echo "Linting project with flake8 ..."
echo "=================================================="

flake8 "$CODE_PATH"

echo "=================================================="
echo
echo "Checking for type errors with mypy ..."
echo "=================================================="

mypy "$CODE_PATH"

echo "=================================================="
echo "Done running mypy."
