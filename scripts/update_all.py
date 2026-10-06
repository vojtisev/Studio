#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Orchestrace aktualizace dat po ručních exportech a browser extrakcích."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
SCRIPTS = BASE / "scripts"
VENV_PYTHON = BASE / ".venv" / "bin" / "python"

RC_MONTHLY = DATA / "MKP Studio - Red Circle měsíčně.csv"
YT_MONTHLY = DATA / "MKP Studio - YouTube měsíčně.csv"
STATISTIKA = DATA / "MKP Studio - statistika.csv"
META = DATA / "statistiky_meta.json"
DESC_RAW = DATA / "yt_monthly_desc_raw.json"
ASC_RAW = DATA / "yt_monthly_asc_raw.json"


def python_bin() -> str:
    """Preferuje .venv (pandas/streamlit), jinak aktuální interpret."""
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def mtime_str(path: Path) -> str:
    if not path.exists():
        return "—"
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def run_py(script: Path) -> None:
    subprocess.run([python_bin(), str(script)], cwd=BASE, check=True)


def csv_stats(path: Path, episode_col: str, month_col: str, value_col: str) -> dict | None:
    if not path.exists():
        return None
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    if not rows:
        return None
    episodes = {r[episode_col] for r in rows if r.get(episode_col)}
    months = [r[month_col] for r in rows if r.get(month_col)]
    total = sum(int(r[value_col]) for r in rows if str(r.get(value_col, "")).isdigit())
    return {
        "rows": len(rows),
        "episodes": len(episodes),
        "max_month": max(months) if months else "—",
        "total": total,
    }


def json_points(path: Path) -> int:
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return len(data) if isinstance(data, list) else 0


def main() -> int:
    print("=== MKP Studio – aktualizace dat ===\n")

    has_desc = DESC_RAW.exists()
    has_asc = ASC_RAW.exists()
    has_rc_report = bool(list(DATA.glob("EpisodePerformanceReport_*.csv")))
    has_tabulce = bool(list(DATA.glob("*tabulce*.csv")))

    print("Vstupy ve složce data/:")
    print(f"  RC měsíčně CSV      : {'✓' if RC_MONTHLY.exists() else '—'} ({mtime_str(RC_MONTHLY)})")
    print(f"  YT desc raw JSON    : {'✓' if has_desc else '—'} ({mtime_str(DESC_RAW)}, {json_points(DESC_RAW)} bodů)")
    print(f"  YT asc raw JSON     : {'✓' if has_asc else '—'} ({mtime_str(ASC_RAW)}, {json_points(ASC_RAW)} bodů)")
    print(f"  RC lifetime report  : {'✓' if has_rc_report else '—'}")
    print(f"  YT Data v tabulce   : {'✓' if has_tabulce else '—'}")
    print()

    exit_code = 0

    # B – YouTube měsíční CSV
    if has_desc and has_asc:
        print("→ Sestavuji YouTube měsíční CSV…")
        run_py(SCRIPTS / "build_yt_monthly_csv.py")
        print()
    elif has_desc or has_asc:
        print("⚠ Chybí druhý YT raw soubor (potřebujete desc i asc). Přeskočeno sestavení YT měsíčně.\n")
        exit_code = 1
    else:
        print("ℹ YT raw JSON chybí – přeskočeno sestavení YT měsíčně (spusťte scripts/yt_monthly_browser_extract.js).\n")

    # A – lifetime statistika
    if has_rc_report and has_tabulce:
        print("→ Spouštím combine_usage_data.py (lifetime)…")
        try:
            run_py(BASE / "combine_usage_data.py")
        except subprocess.CalledProcessError as e:
            print(f"⚠ combine_usage_data.py selhal (exit {e.returncode}).")
            if not VENV_PYTHON.exists():
                print("  Chybí .venv — jednorázově:")
                print("    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
            else:
                print("  Zkuste: .venv/bin/pip install -r requirements.txt")
            exit_code = 1
        print()
    else:
        missing = []
        if not has_rc_report:
            missing.append("EpisodePerformanceReport_*.csv")
        if not has_tabulce:
            missing.append("Data v tabulce*.csv")
        print(f"ℹ Lifetime přeskočeno – chybí: {', '.join(missing)}\n")

    # Kontrola výstupů
    print("=== Kontrola výstupů ===")
    yt = csv_stats(YT_MONTHLY, "Epizoda", "Měsíc", "YouTube_Zhlédnutí")
    rc = csv_stats(RC_MONTHLY, "Epizoda", "Měsíc", "RedCircle_Downloads")

    if yt:
        warn = " ⚠" if yt["episodes"] < 100 else ""
        print(
            f"  YouTube měsíčně : {yt['rows']} řádků, {yt['episodes']} epizod, "
            f"max {yt['max_month']}, součet {yt['total']}{warn}"
        )
        if yt["episodes"] < 20:
            print("    ⚠ Málo epizod – možná export z grafu místo browser extrakce.")
            exit_code = 1
    else:
        print("  YouTube měsíčně : chybí")
        exit_code = 1

    if rc:
        print(
            f"  RC měsíčně       : {rc['rows']} řádků, {rc['episodes']} epizod, "
            f"max {rc['max_month']}, součet {rc['total']}"
        )
    else:
        print("  RC měsíčně       : chybí (spusťte scripts/rc_monthly_browser_extract.js)")
        exit_code = 1

    if STATISTIKA.exists():
        stat_rows = list(csv.DictReader(STATISTIKA.open(encoding="utf-8-sig")))
        print(f"  statistika.csv   : {len(stat_rows)} epizod ({mtime_str(STATISTIKA)})")
    else:
        print("  statistika.csv   : chybí")

    if META.exists():
        meta = json.loads(META.read_text(encoding="utf-8"))
        print(
            f"  statistiky_meta  : posledni_mesic={meta.get('posledni_mesic_statistik')}, "
            f"zdroj={meta.get('zdroj')}"
        )

    print("\n=== Hotovo ===")
    print("Obnovte dashboard: F5 ve Streamlitu, nebo ./run_media_analytics.sh")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
