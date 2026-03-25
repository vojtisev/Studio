# Návod pro aktualizaci statistik podcastů

## Co skript dělá
Kombinuje data z YouTube Studio a Red Circle do jednoho přehledného souboru s celkovým využitím epizod.

## Jak připravit data pro spuštění

### 1. Stáhněte soubory z analytik

**YouTube Studio:**
- Stáhněte soubor **"Data v tabulce.csv"** (export z YouTube Studio)
- Volitelně: Stáhněte soubor **"Data v grafu.csv"** (pokud máte časová data)

**Red Circle:**
- Stáhněte soubor **"EpisodePerformanceReport_*.csv"** (název obsahuje datum, např. `EpisodePerformanceReport_2025_06_01_to_2025_12_31.csv`)

### 2. Uložte soubory do složky
Všechny soubory uložte do stejné složky, kde je skript `combine_usage_data.py`.

### 3. Spusťte skript
```bash
python3 combine_usage_data.py
```

## Výstup
Skript vytvoří soubor **"MKP Studio - statistika.csv"** s následujícími sloupci:
- `PodcastName` - název pořadu
- `Epizoda` - název epizody
- `Datum_publikování` - datum zveřejnění
- `YouTube_Zhlédnutí` - celkový počet zhlédnutí
- `RedCircle_Downloads` - celkový počet downloads
- `Celkové_využití` - součet obou metrik

## Automatické vyhledávání souborů
Skript automaticky najde:
- ✅ YouTube soubory podle názvu (`*tabulce*.csv`, `*grafu*.csv`)
- ✅ Nejnovější Red Circle soubor (`EpisodePerformanceReport_*.csv`)

**Poznámka:** Pokud máte více Red Circle souborů, skript automaticky použije ten nejnovější (podle data modifikace souboru).

## Tipy
- Pokud máte starší soubory, můžete je ponechat ve složce - skript použije nejnovější
- Soubor "Data v grafu.csv" je volitelný - pokud ho nemáte, skript použije celkové hodnoty z "Data v tabulce.csv"

