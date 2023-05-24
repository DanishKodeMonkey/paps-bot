#!/usr/bin/env bash

echo "Checking code formatting with 'black --check'"
echo "If this check fails, run the ci/format.sh script to format the code."
echo "=================================================="

black --check "paps_bot" && echo "Code is formatted with black." || exit 1

echo "=================================================="
echo "Code is formatted using black."
