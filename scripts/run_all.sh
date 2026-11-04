#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python -m ab_toolkit all
echo "Open web/index.html in your browser for the calculator"
