#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN=${PYTHON_BIN:-python3}

if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "✅ Environment ready. If you're on THI Wi-Fi/VPN, start the app with:"
echo "   streamlit run app.py"
