#!/bin/bash
# Spouštění Streamlit aplikace pro analýzu online obsahu

cd "$(dirname "$0")"
python3 -m streamlit run streamlit_media_analytics.py

