# Rychlá aktualizace statistik (≈15–20 min)

Checklist pro měsíční obnovu dashboardu. Detailní vysvětlení: `Jak na aktualizaci statistiky podcastů.md`.

---

## 1. Exporty do `data/` (lifetime)

| Platforma | Kde | Soubor |
|-----------|-----|--------|
| **YouTube** | Studio → Analytics → rozšířený režim → MKP Studio → export **Data v tabulce** | `Data v tabulce.csv` (nebo kopie) |
| **Red Circle** | Stats → Episode Performance → All time → export report | `EpisodePerformanceReport_*.csv` |

⚠️ **Nepoužívejte** export „Data v grafu“ — má jen ~5 videí.

---

## 2. Red Circle – měsíční data (≈2 min)

1. Přihlaste se na [Red Circle Stats](https://app.redcircle.com/stats/downloads)
2. **Episode Performance** → **Select Date Range** + **Month** (ne Since Published)
3. Období: **All time** (do dneška)
4. DevTools (F12) → **Console** → vložte obsah souboru **`scripts/rc_monthly_browser_extract.js`** → Enter
5. Stáhne se `MKP Studio - Red Circle měsíčně.csv` → přesuňte do **`data/`**

---

## 3. YouTube – měsíční data (≈5 min)

**Příprava:** Studio → Analytics → rozšířený režim:

- Entita **182 MKP Studio**
- Období **Od začátku** (do konce minulého měsíce)
- Granularita **Měsíční**, dimenze **Video**
- Seřazeno podle **Zhlédnutí sestupně** (DESC)

**Krok A – DESC**

1. URL musí obsahovat `o_direction=ANALYTICS_ORDER_DIRECTION_DESC`
2. Console → vložte **`scripts/yt_monthly_browser_extract.js`** → Enter (≈2 min)
3. Uložte `yt_monthly_desc_raw.json` (Safari nabídne jeden soubor — to je správně)

**Krok B – ASC (stejná záložka)**

1. **Vyčistěte konzoli:** `Cmd+K` (nebo ikona koše) — YouTube jinak konzoli zahlcuje a nejde vložit skript
2. Přepněte řazení na **vzestupné** ve stejné záložce: klik na sloupec **Zhlédnutí**, nebo ASC URL do **adresního řádku** téže záložky (ne nové okno)
3. Po načtení tabulky: znovu `Cmd+K` → klikněte do **řádku dole** v konzoli → vložte skript → Enter
4. Uložte `yt_monthly_asc_raw.json` → oba JSON do **`data/`**

> ~100 videí má skutečný měsíční rozpad; zbytek doplní skript z tabulky (fallback).
> Safari: jeden soubor za běh (DESC, pak ASC) — záměr.

---

## 4. Jeden příkaz

```bash
cd ~/Cursor\ Workspace/MKP/Studio
python3 scripts/update_all.py
```

Skript:

- sestaví `MKP Studio - YouTube měsíčně.csv` + `statistiky_meta.json`
- spustí `combine_usage_data.py` (lifetime), pokud jsou exporty z kroku 1
- vypíše kontrolní souhrn

---

## 5. Dashboard

**F5** ve Streamlitu, nebo:

```bash
./run_media_analytics.sh
```

---

## Kontrola (očekávání)

| Soubor | Řádově |
|--------|--------|
| YouTube měsíčně | 150+ epizod, stovky řádků |
| RC měsíčně | 170+ epizod |
| statistiky_meta → zdroj | obsahuje `browser_extract` |

---

## Když něco chybí

| Problém | Řešení |
|---------|--------|
| YT skript: „tabulka se nenačetla“ | Počkejte na plné načtení, zkontrolujte filtr MKP Studio + Měsíční |
| YT skript: „chybí DESC v localStorage“ | ASC jste otevřeli v novém okně — vraťte se na DESC ve stejné záložce a spusťte skript znovu |
| Safari stáhne jen jeden soubor | Normální: jeden při DESC, druhý při ASC |
| Konzole zahlcená, nejde vložit skript | `Cmd+K` (Clear), kliknout do řádku dole, teprve pak vložit |
| Málo YT epizod (<20) | Nepřepisujte browser CSV exportem z grafu |
| `update_all.py` přeskočí lifetime | Doplňte exporty z kroku 1 do `data/` |
