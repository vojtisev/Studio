#!/bin/bash
# Spouštění Streamlit aplikace pro analýzu online obsahu

cd "$(dirname "$0")"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  echo "Chybí .venv. Jednorázově spusťte:"
  echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  PYTHON="python3"
fi

"$PYTHON" -m streamlit run streamlit_media_analytics.py
