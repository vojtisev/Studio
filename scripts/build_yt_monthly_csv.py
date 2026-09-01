#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sestaví MKP Studio - YouTube měsíčně.csv z browser extrakce DESC+ASC + fallback."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
OUT = DATA / "MKP Studio - YouTube měsíčně.csv"
META = DATA / "statistiky_meta.json"
DESC_RAW = DATA / "yt_monthly_desc_raw.json"
ASC_RAW = DATA / "yt_monthly_asc_raw.json"


def norm_title(s: str) -> str:
    s = str(s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def load_title_maps() -> tuple[dict[str, str], dict[str, int]]:
    """title_norm -> video_id, title_norm -> lifetime views."""
    id_by_title: dict[str, str] = {}
    views_by_title: dict[str, int] = {}

    for path in (DATA / "yt_video_ids_all.json", DATA / "yt_video_ids_missing.json"):
        if not path.exists():
            continue
        for row in json.loads(path.read_text(encoding="utf-8")):
            t = norm_title(row.get("title", ""))
            if t:
                id_by_title[t] = row["id"]
                views_by_title[t] = int(row.get("views") or 0)

    tabulce = max(DATA.glob("*tabulce*.csv"), key=lambda p: p.stat().st_mtime, default=None)
    if tabulce:
        for row in csv.DictReader(tabulce.open(encoding="utf-8-sig")):
            title = row.get("Název videa") or ""
            t = norm_title(title)
            if not t:
                continue
            obsah = (row.get("Obsah") or "").strip()
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", obsah):
                id_by_title.setdefault(t, obsah)
            else:
                m = re.search(
                    r"https?://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]{11})", obsah
                )
                if m:
                    id_by_title.setdefault(t, m.group(1))
            try:
                views_by_title.setdefault(t, int(str(row.get("Zhlédnutí", "0")).replace(" ", "")))
            except ValueError:
                pass

    return id_by_title, views_by_title


def load_podcast_map() -> dict[str, str]:
    stat = DATA / "MKP Studio - statistika.csv"
    out: dict[str, str] = {}
    if not stat.exists():
        return out
    for row in csv.DictReader(stat.open(encoding="utf-8-sig")):
        t = norm_title(row.get("Epizoda", ""))
        if t:
            out[t] = row.get("PodcastName", "") or ""
    return out


def fix_vid(row: dict, id_by_title: dict[str, str]) -> str:
    vid = (row.get("vid") or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        return vid
    t = norm_title(row.get("title", ""))
    return id_by_title.get(t, vid)


def publish_month(title: str, tabulce_rows: list[dict]) -> str | None:
    t = norm_title(title)
    for row in tabulce_rows:
        rt = norm_title(row.get("Název videa") or row.get("Obsah") or "")
        if rt != t:
            continue
        raw = (row.get("Čas zveřejnění videa") or "").strip()
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S", "%b %d, %Y"):
            try:
                return datetime.strptime(raw[:19] if fmt != "%b %d, %Y" else raw, fmt).strftime(
                    "%Y-%m"
                )
            except ValueError:
                continue
    return None


def load_raw(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    id_by_title, views_by_title = load_title_maps()
    podcast_by_title = load_podcast_map()

    tabulce_path = max(DATA.glob("*tabulce*.csv"), key=lambda p: p.stat().st_mtime)
    tabulce_rows = list(csv.DictReader(tabulce_path.open(encoding="utf-8-sig")))

    monthly: dict[tuple[str, str], dict] = {}

    for src in load_raw(DESC_RAW) + load_raw(ASC_RAW):
        title = (src.get("title") or "").strip()
        month = (src.get("month") or "").strip()
        views = int(src.get("views") or 0)
        if not title or not month or views <= 0:
            continue
        vid = fix_vid(src, id_by_title)
        key = (norm_title(title), month)
        monthly[key] = {
            "Epizoda": title,
            "Měsíc": month,
            "YouTube_Zhlédnutí": views,
            "PodcastName": podcast_by_title.get(norm_title(title), ""),
            "_vid": vid,
            "_source": "browser",
        }

    covered_titles = {k[0] for k in monthly}

    fallback_count = 0
    for row in tabulce_rows:
        title = (row.get("Název videa") or "").strip()
        if not title or (row.get("Obsah") or "").strip().lower() == "celkem":
            continue
        t = norm_title(title)
        if t in covered_titles:
            continue
        try:
            views = int(str(row.get("Zhlédnutí", "0")).replace(" ", ""))
        except ValueError:
            views = 0
        if views <= 0:
            continue
        month = publish_month(title, tabulce_rows)
        if not month:
            continue
        key = (t, month)
        if key in monthly:
            continue
        monthly[key] = {
            "Epizoda": title,
            "Měsíc": month,
            "YouTube_Zhlédnutí": views,
            "PodcastName": podcast_by_title.get(t, ""),
            "_vid": id_by_title.get(t, (row.get("Obsah") or "").strip()),
            "_source": "fallback_publish_month",
        }
        fallback_count += 1
        covered_titles.add(t)

    rows = sorted(monthly.values(), key=lambda r: (r["Epizoda"], r["Měsíc"]))
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Epizoda", "Měsíc", "YouTube_Zhlédnutí", "PodcastName"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})

    episodes = len({r["Epizoda"] for r in rows})
    browser_eps = len({r["Epizoda"] for r in rows if r.get("_source") == "browser"})
    max_month = max(r["Měsíc"] for r in rows) if rows else "2026-08"
    total_views = sum(r["YouTube_Zhlédnutí"] for r in rows)

    meta = {
        "posledni_mesic_statistik": max_month,
        "zdroj": f"youtube_studio_browser_extract_{datetime.now().strftime('%Y-%m-%d')}",
        "poznamka": f"browser {browser_eps} epizod + fallback {fallback_count} epizod, celkem {episodes} epizod",
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Zapsáno {len(rows)} řádků, {episodes} epizod (browser ~{browser_eps}, fallback {fallback_count})")
    print(f"Celkem zhlédnutí v měsíčním CSV: {total_views}")
    print(f"Poslední měsíc: {max_month}")
    print(f"Výstup: {OUT}")


if __name__ == "__main__":
    main()
