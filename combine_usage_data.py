#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skript pro kombinaci dat z YouTube a Red Circle
Kombinuje zhlédnutí z YouTube a Downloads z Red Circle podle názvů epizod
a vytváří celkové součty pro každou epizodu
"""

import json
import pandas as pd
import numpy as np
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def extract_keywords(name):
    """Extrahuje klíčová slova z názvu"""
    if pd.isna(name):
        return set()
    name = str(name).lower()
    # Odstranění interpunkce a speciálních znaků
    name = re.sub(r'[^\w\s]', ' ', name)
    # Rozdělení na slova
    words = name.split()
    # Odstranění krátkých slov (méně než 3 znaky)
    words = [w for w in words if len(w) >= 3]
    return set(words)

def find_matching_episodes(yt_name, rc_names):
    """Najde nejlepší shodu mezi YouTube názvem a Red Circle názvy pomocí klíčových slov"""
    if pd.isna(yt_name):
        return None
    
    yt_keywords = extract_keywords(yt_name)
    if not yt_keywords:
        return None
    
    best_match = None
    best_score = 0
    
    for rc_name in rc_names:
        if pd.isna(rc_name):
            continue
        
        rc_keywords = extract_keywords(rc_name)
        if not rc_keywords:
            continue
        
        # Počet společných klíčových slov
        common = len(yt_keywords & rc_keywords)
        total = len(yt_keywords | rc_keywords)
        if total > 0:
            score = common / total
            if score > best_score and score >= 0.5:  # Minimální podobnost 50%
                best_score = score
                best_match = rc_name
    
    return best_match

def main():
    print("Načítám data...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Načtení YouTube dat - hlavní soubor pro párování (složka data/)
    yt_table_files = list(DATA_DIR.glob('*tabulce*.csv'))
    if not yt_table_files:
        print(f"CHYBA: V {DATA_DIR.relative_to(BASE_DIR)}/ nebyl nalezen soubor '*tabulce*.csv' (export YouTube).")
        return
    yt_table_file = max(yt_table_files, key=lambda p: p.stat().st_mtime)
    print(f"Načítám YouTube soubor pro párování: {yt_table_file.name}")
    yt_table_df = pd.read_csv(yt_table_file, encoding='utf-8')
    
    # Načtení YouTube dat s časovými údaji – měsíční formát (Datum = YYYY-MM) nebo denní
    yt_graph_files = list(DATA_DIR.glob('*grafu*.csv'))
    yt_graph_df = None
    if yt_graph_files:
        yt_graph_file = max(yt_graph_files, key=lambda p: p.stat().st_mtime)
        print(f"Načítám YouTube soubor s časovými údaji: {yt_graph_file.name}")
        yt_graph_df = pd.read_csv(yt_graph_file, encoding='utf-8')
        # Podpora měsíčního formátu (2025-06) i denního
        datums = yt_graph_df['Datum'].astype(str).str.strip()
        monthly_mask = datums.str.match(r'^\d{4}-\d{2}$')
        yt_graph_df.loc[monthly_mask, 'Datum'] = datums[monthly_mask] + '-01'
        yt_graph_df['Datum'] = pd.to_datetime(yt_graph_df['Datum'], errors='coerce')
        yt_graph_df = yt_graph_df.dropna(subset=['Datum', 'Název videa'])
    
    # Načtení Red Circle dat - automaticky najde nejnovější soubor ve složce data/
    rc_files = list(DATA_DIR.glob('EpisodePerformanceReport_*.csv'))
    if not rc_files:
        print(f"CHYBA: V {DATA_DIR.relative_to(BASE_DIR)}/ nebyl nalezen soubor 'EpisodePerformanceReport_*.csv'.")
        return
    rc_file = max(rc_files, key=lambda p: p.stat().st_mtime)
    print(f"Načítám Red Circle soubor: {rc_file.name}")
    rc_df = pd.read_csv(rc_file)
    rc_df['PublishDate'] = pd.to_datetime(rc_df['PublishDate'], errors='coerce')
    
    print(f"\nYouTube data (tabulka): {yt_table_df.shape}")
    if yt_graph_df is not None:
        print(f"YouTube data (graf): {yt_graph_df.shape}")
    print(f"Red Circle data: {rc_df.shape}")
    
    # Získání unikátních názvů epizod z Red Circle
    rc_episodes = rc_df['EpisodeName'].unique()
    print(f"\nPočet unikátních epizod v Red Circle: {len(rc_episodes)}")
    
    # Vytvoření mapování mezi YouTube a Red Circle názvy
    print("\nHledám shodné epizody...")
    episode_mapping = {}
    matched_count = 0
    
    yt_episodes = yt_table_df['Název videa'].dropna().unique()
    for yt_episode in yt_episodes:
        match = find_matching_episodes(yt_episode, rc_episodes)
        if match:
            episode_mapping[yt_episode] = match
            matched_count += 1
            if matched_count <= 10:  # Zobrazíme prvních 10 shod
                print(f"  ✓ '{yt_episode[:60]}...' <-> '{match[:60]}...'")
    
    print(f"\nNalezeno {matched_count} shodných epizod z {len(yt_episodes)} YouTube epizod")
    
    # Zjištění epizod, které se nespárovaly (existují jen na jedné platformě)
    matched_yt_episodes = set(episode_mapping.keys())
    matched_rc_episodes = set(episode_mapping.values())
    all_yt_episodes = set(yt_episodes)
    all_rc_episodes = set(rc_episodes)
    
    unmatched_yt_episodes = sorted(all_yt_episodes - matched_yt_episodes)
    unmatched_rc_episodes = sorted(all_rc_episodes - matched_rc_episodes)
    
    print(f"\nYouTube epizody bez shody v Red Circle: {len(unmatched_yt_episodes)}")
    for ep in unmatched_yt_episodes[:10]:
        print(f"  YT pouze: '{ep[:80]}'")
    
    print(f"\nRed Circle epizody bez shody na YouTube: {len(unmatched_rc_episodes)}")
    for ep in unmatched_rc_episodes[:10]:
        print(f"  RC pouze: '{ep[:80]}'")
    
    # Vytvoření kombinovaného datasetu
    print("\nVytvářím kombinovaný dataset...")
    
    combined_data = []
    
    # Pro každou shodnou epizodu (existuje na obou platformách)
    for yt_name, rc_name in episode_mapping.items():
        # Red Circle data pro tuto epizodu
        rc_episode_data = rc_df[rc_df['EpisodeName'] == rc_name].copy()
        
        # Red Circle downloads (celkové)
        rc_downloads = 0
        rc_publish_date = None
        rc_podcast_name = None
        if len(rc_episode_data) > 0:
            rc_downloads = rc_episode_data.iloc[0]['Downloads']
            rc_publish_date = rc_episode_data.iloc[0]['PublishDate']
            rc_podcast_name = rc_episode_data.iloc[0]['PodcastName']
        
        # YouTube data - zkusíme najít časová data v grafu a sečteme je
        youtube_total = 0
        if yt_graph_df is not None:
            yt_episode_data = yt_graph_df[yt_graph_df['Název videa'] == yt_name].copy()
            if len(yt_episode_data) > 0:
                # Máme časová data - sečteme všechna denní zhlédnutí
                youtube_total = yt_episode_data['Zhlédnutí'].sum()
        
        # Pokud nemáme časová data nebo součet je 0, použijeme hodnotu z tabulky
        if youtube_total == 0:
            yt_table_episode = yt_table_df[yt_table_df['Název videa'] == yt_name]
            if len(yt_table_episode) > 0:
                youtube_total = yt_table_episode['Zhlédnutí'].sum() if 'Zhlédnutí' in yt_table_episode.columns else 0
        
        # Formátování data publikování
        publish_date_str = ''
        if pd.notna(rc_publish_date):
            try:
                publish_date_str = pd.Timestamp(rc_publish_date).strftime('%Y-%m-%d')
            except:
                publish_date_str = str(rc_publish_date) if rc_publish_date else ''
        
        # Vytvoříme jeden řádek s celkovými hodnotami
        combined_data.append({
            'PodcastName': rc_podcast_name if pd.notna(rc_podcast_name) else '',
            'Epizoda': yt_name,
            'Datum_publikování': publish_date_str,
            'YouTube_Zhlédnutí': int(youtube_total) if not pd.isna(youtube_total) else 0,
            'RedCircle_Downloads': int(rc_downloads) if not pd.isna(rc_downloads) else 0,
            'Celkové_využití': int(youtube_total + rc_downloads) if not (pd.isna(youtube_total) or pd.isna(rc_downloads)) else 0
        })
    
    # YouTube epizody bez shody v Red Circle – ponecháme je s nulovými downloads
    for yt_name in unmatched_yt_episodes:
        # YouTube data - zkusíme najít časová data v grafu a sečteme je
        youtube_total = 0
        if yt_graph_df is not None:
            yt_episode_data = yt_graph_df[yt_graph_df['Název videa'] == yt_name].copy()
            if len(yt_episode_data) > 0:
                youtube_total = yt_episode_data['Zhlédnutí'].sum()
        
        # Pokud nemáme časová data nebo součet je 0, použijeme hodnotu z tabulky
        if youtube_total == 0:
            yt_table_episode = yt_table_df[yt_table_df['Název videa'] == yt_name]
            if len(yt_table_episode) > 0:
                youtube_total = yt_table_episode['Zhlédnutí'].sum() if 'Zhlédnutí' in yt_table_episode.columns else 0
        
        combined_data.append({
            'PodcastName': '',
            'Epizoda': yt_name,
            'Datum_publikování': '',
            'YouTube_Zhlédnutí': int(youtube_total) if not pd.isna(youtube_total) else 0,
            'RedCircle_Downloads': 0,
            'Celkové_využití': int(youtube_total) if not pd.isna(youtube_total) else 0
        })
    
    # Red Circle epizody bez shody na YouTube – ponecháme je s nulovými YouTube zhlédnutími
    for rc_name in unmatched_rc_episodes:
        rc_episode_data = rc_df[rc_df['EpisodeName'] == rc_name].copy()
        
        rc_downloads = 0
        rc_publish_date = None
        rc_podcast_name = None
        if len(rc_episode_data) > 0:
            rc_downloads = rc_episode_data.iloc[0]['Downloads']
            rc_publish_date = rc_episode_data.iloc[0]['PublishDate']
            rc_podcast_name = rc_episode_data.iloc[0]['PodcastName']
        
        publish_date_str = ''
        if pd.notna(rc_publish_date):
            try:
                publish_date_str = pd.Timestamp(rc_publish_date).strftime('%Y-%m-%d')
            except:
                publish_date_str = str(rc_publish_date) if rc_publish_date else ''
        
        combined_data.append({
            'PodcastName': rc_podcast_name if pd.notna(rc_podcast_name) else '',
            'Epizoda': rc_name,
            'Datum_publikování': publish_date_str,
            'YouTube_Zhlédnutí': 0,
            'RedCircle_Downloads': int(rc_downloads) if not pd.isna(rc_downloads) else 0,
            'Celkové_využití': int(rc_downloads) if not pd.isna(rc_downloads) else 0
        })
    
    # Vytvoření DataFrame
    result_df = pd.DataFrame(combined_data)
    
    if len(result_df) == 0:
        print("\nCHYBA: Nepodařilo se vytvořit kombinovaný dataset!")
        return
    
    # Seřazení podle podcastu a epizody
    result_df = result_df.sort_values(['PodcastName', 'Epizoda'])
    
    # Uložení výsledku
    output_file = DATA_DIR / 'MKP Studio - statistika.csv'
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # Export měsíčních YouTube dat (RedCircle měsíční rozpad nemáme)
    if yt_graph_df is not None and len(yt_graph_df) > 0:
        monthly_df = yt_graph_df[['Název videa', 'Datum', 'Zhlédnutí']].copy()
        monthly_df = monthly_df.rename(columns={
            'Název videa': 'Epizoda',
            'Datum': 'Měsíc',
            'Zhlédnutí': 'YouTube_Zhlédnutí'
        })
        monthly_df['Měsíc'] = monthly_df['Měsíc'].dt.strftime('%Y-%m')
        # Přidáme PodcastName z výsledné tabulky (epizoda -> pořad)
        ep_to_podcast = result_df[['Epizoda', 'PodcastName']].drop_duplicates('Epizoda').set_index('Epizoda')['PodcastName']
        monthly_df['PodcastName'] = monthly_df['Epizoda'].map(ep_to_podcast).fillna('')
        monthly_file = DATA_DIR / 'MKP Studio - YouTube měsíčně.csv'
        monthly_df.to_csv(monthly_file, index=False, encoding='utf-8-sig')
        print(f"✓ Měsíční YouTube data uložena do: {monthly_file.relative_to(BASE_DIR)} ({len(monthly_df)} řádků)")
        last_m = monthly_df["Měsíc"].max()
        meta_path = DATA_DIR / "statistiky_meta.json"
        meta = {
            "posledni_mesic_statistik": last_m,
            "zdroj": "youtube_mesicne_po_exportu",
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ Meta období statistik: {meta_path.relative_to(BASE_DIR)} (poslední měsíc: {last_m})")
    
    print(f"\n✓ Výsledek uložen do: {output_file.relative_to(BASE_DIR)}")
    print(f"\nShrnutí:")
    print(f"  Počet epizod: {result_df['Epizoda'].nunique()}")
    print(f"  Počet záznamů: {len(result_df)}")
    print(f"  Celkové využití (součet): {result_df['Celkové_využití'].sum():,}")
    print(f"\nPrvních 15 řádků výsledku:")
    print(result_df.head(15).to_string())
    
    return result_df

if __name__ == '__main__':
    main()
