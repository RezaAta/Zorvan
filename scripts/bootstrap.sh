#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script for UNIX-like environments
# Usage: ./scripts/bootstrap.sh [--gui]
INSTALL_GUI=false
if [ "${1:-}" = "--gui" ]; then
    INSTALL_GUI=true
fi

VENV_PATH=".venv"
if [ ! -d "$VENV_PATH" ]; then
    python -m venv "$VENV_PATH"
fi

# shellcheck disable=SC1091
source "$VENV_PATH/bin/activate"
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi
if [ -f requirements_dev.txt ]; then
    pip install -r requirements_dev.txt
fi
if [ "$INSTALL_GUI" = true ] && [ -f requirements_gui.txt ]; then
    pip install -r requirements_gui.txt
fi
pip install -e .

echo "Bootstrap complete. Activate the venv with 'source .venv/bin/activate' and run pytest."
