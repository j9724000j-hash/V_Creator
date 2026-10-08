#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo 'Checking outdated packages only. Updates must be reviewed, pinned, tested and committed.'
.venv/bin/python -m pip list --outdated
npm outdated || [[ $? == 1 ]]
