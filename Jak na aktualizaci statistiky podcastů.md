# Návod pro aktualizaci statistik podcastů

## Co skript dělá
Kombinuje data z YouTube Studio a Red Circle do jednoho přehledného souboru s celkovým využitím epizod.

## Kam ukládat soubory (po přesunu projektu)
**Vstupní exporty** (YouTube, Red Circle) ukládej do podsložky **`data/`** uvnitř projektu:

**`~/Cursor Workspace/MKP/Studio/data/`**

Skripty (`combine_usage_data.py`, `streamlit_media_analytics.py`) zůstávají v kořeni projektu (`Studio/`). **Výstupní soubory** (`MKP Studio - statistika.csv`, případně `MKP Studio - YouTube měsíčně.csv`) skript zapisuje také do **`data/`**.

Starší exporty můžeš v `data/` nechávat – u více souborů stejného typu skript bere **nejnovější podle data úpravy souboru** (kromě výstupů, které se při běhu přepisují).

> Skript nepotřebuje běžet z konkrétní složky – cesty si bere sám od souboru `combine_usage_data.py`. Stačí: `python3 combine_usage_data.py` z adresáře `Studio/`, nebo plná cesta ke skriptu.

## Období – co přesně platí
Skript **nesestavuje vlastní časové období**; bere vždy to, co je uvnitř stažených souborů.

| Zdroj | Co v exportu obvykle je | Doporučení při aktualizaci |
|--------|---------------------------|----------------------------|
| **YouTube – Data v tabulce** | Celková zhlédnutí na video (podle toho, jaký rozsah zvolíš v exportu v YouTube Studio – často „celé období“ / všechna dostupná data). | Pro srovnání s Red Circle používej export, který pokrývá **stejnou logiku** jako podcastová analytika (typicky kompletní historie kanálu nebo stejné období jako u Red Circle). |
| **YouTube – Data v grafu** | Měsíční (nebo denní) rozpad zhlédnutí – skript je sečte po epizodách a použije pro součty + soubor `MKP Studio - YouTube měsíčně.csv`. | Volitelné; pokud chybí, berou se součty jen z tabulky. |
| **Red Circle – EpisodePerformanceReport** | V názvu souboru je **období reportu** (např. `2025_06_01_to_2026_01_31`). Uvnitř jsou **aktuální kumulativní stažení** epizod v tom kontextu, jak Red Circle report generuje. | Stáhni **nejnovější** report z rozhraní. Ve složce můžeš mít více `EpisodePerformanceReport_*.csv` – skript **automaticky vezme soubor s nejnovějším datem úpravy** na disku (ne podle textu v názvu). |

**Shrnutí:** Období si vybíráš **v YouTube Studio a v Red Circle** při exportu. Skript jen spojí to, co v těch souborech je. Chceš-li „statistiky k dnešku“, stáhni čerstvé exporty z obou platforem a ulož je do **`Studio/data/`** (případně přepiš starší soubory stejných jmen).

## Jak připravit data pro spuštění

### 1. Stáhněte soubory z analytik

**YouTube Studio:**
- Stáhněte soubor **"Data v tabulce.csv"** (export z YouTube Studio)
- Volitelně: Stáhněte soubor **"Data v grafu.csv"** (měsíční / časový rozpad zhlédnutí)

**Red Circle:**
- Stáhněte soubor **"EpisodePerformanceReport_*.csv"** (název obsahuje datum, např. `EpisodePerformanceReport_2025_06_01_to_2025_12_31.csv`)

### 2. Uložte soubory do složky
Exporty uložte do **`~/Cursor Workspace/MKP/Studio/data/`** (ne do kořene projektu).

### 3. Spusťte skript
```bash
cd "~/Cursor Workspace/MKP/Studio"
python3 combine_usage_data.py
```

## Výstup
Skript vytvoří (ve složce **`data/`**) soubor **`MKP Studio - statistika.csv`** s následujícími sloupci:
- `PodcastName` - název pořadu
- `Epizoda` - název epizody
- `Datum_publikování` - datum zveřejnění
- `YouTube_Zhlédnutí` - celkový počet zhlédnutí
- `RedCircle_Downloads` - celkový počet downloads
- `Celkové_využití` - součet obou metrik

## Automatické vyhledávání souborů
Skript hledá soubory ve složce **`data/`**:
- ✅ YouTube soubory podle názvu (`*tabulce*.csv`, `*grafu*.csv`) – pokud jich je víc, vezme **nejnovější podle data úpravy**
- ✅ Nejnovější Red Circle soubor (`EpisodePerformanceReport_*.csv`) podle data úpravy souboru

## Tipy
- Pokud máte starší soubory, můžete je ponechat ve složce - skript použije nejnovější
- Soubor "Data v grafu.csv" je volitelný - pokud ho nemáte, skript použije celkové hodnoty z "Data v tabulce.csv"

