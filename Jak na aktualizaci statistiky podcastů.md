# Návod pro aktualizaci statistik podcastů

## Rychlá aktualizace (doporučeno)

Měsíční checklist na jedné stránce: **`scripts/Aktualizace.md`**

1. Exporty lifetime do `data/` (YT tabulka + RC report)
2. Red Circle: `scripts/rc_monthly_browser_extract.js` v konzoli → CSV do `data/`
3. YouTube: `scripts/yt_monthly_browser_extract.js` 2× (DESC, pak ASC) → JSON do `data/`
4. `python3 scripts/update_all.py`
5. F5 ve Streamlitu

Detailní vysvětlení a varování níže.

---

## Co skript dělá

`combine_usage_data.py` kombinuje **lifetime** data z YouTube Studio a Red Circle do souboru `MKP Studio - statistika.csv` (celkové zhlédnutí + stažení po epizodách).

**Měsíční data** pro ROI v čase, trend a měsíční top **skript nevytváří spolehlivě** — připravují se **samostatně přes browser extrakci** (viz níže). Oficiální exporty na obou platformách pro měsíční rozpad nestačí.

---

## Dva typy aktualizace (vždy oba pro plný dashboard)

| Typ | Co aktualizuje | Jak | Výstup |
| --- | --- | --- | --- |
| **A – lifetime součty** | Přehled, top epizody, statické ROI | CSV exporty + `combine_usage_data.py` | `MKP Studio - statistika.csv` |
| **B – měsíční rozpad** | ROI v čase, trend, měsíční top | Browser extrakce (YouTube + Red Circle zvlášť) | `MKP Studio - YouTube měsíčně.csv`, `MKP Studio - Red Circle měsíčně.csv`, `statistiky_meta.json` |

Bez **B** zůstanou lifetime metriky aktuální, ale časové grafy budou podle starých měsíčních souborů.

---

## Proč ne stačí „Data v grafu.csv“ (YouTube)

Export **Data v grafu** z YouTube Studia obsahuje měsíční řady jen pro **videa vybraná v porovnávacím grafu** — typicky **max. ~5 videí** (limit checkboxů v UI), ne celý katalog ~160+ epizod.

`combine_usage_data.py` z grafu sice umí zapsat `MKP Studio - YouTube měsíčně.csv`, ale **při běžné aktualizaci to nepoužívejte** — přepsalo by to kvalitní browser soubor neúplnými daty. Skript takový přepis **přeskakuje**, pokud už existuje browser extrakce (viz níže).

Pro měsíční YouTube data proto platí **browser extrakce** (krok 7).

---

## Princip práce s časovým obdobím

Na obou platformách u lifetime exportů vycházíme z rozsahu **od nejdřívějšího data po současnost** — pracujeme s jedním aktuálním souborem od každé platformy, historii neskládáme z více exportů.

- **YouTube Studio – tabulka:** uložený filtr v Analytics; při aktualizaci **doplň nové pořady** od minula (objeví se nahoře).
- **Red Circle – lifetime report:** všechny podcasty, nejširší rozsah.

Skript **nepřepisuje období** — bere obsah posledních stažených CSV ve složce `data/`.

---

## Kam ukládat soubory

**`~/Cursor Workspace/MKP/Studio/data/`**

Skripty zůstávají v kořeni projektu (`Studio/`).

Starší exporty ve `data/` můžeš nechat — skript bere **nejnovější podle data úpravy** souboru (kromě výstupů, které sám přepisuje).

> Stačí: `python3 combine_usage_data.py` z adresáře `Studio/`.

---

## Období – technický význam

| Zdroj | Co v exportu je | Poznámka |
| --- | --- | --- |
| **YouTube – Data v tabulce** | Celková zhlédnutí na video (lifetime). | Filtr doplňuj o nové pořady. |
| **YouTube – Data v grafu** | Měsíční rozpad — ale jen pro **vybraná videa v grafu** (~5). | **Nepoužívat** pro měsíční CSV dashboardu; jen případně pro kontrolu. |
| **YouTube – browser extrakce** | Měsíční zhlédnutí po epizodách z `timelineChartSpec` ve Studiu. | Aktuální zdroj pro `MKP Studio - YouTube měsíčně.csv` (krok 7). |
| **Red Circle – EpisodePerformanceReport** | Lifetime stažení po epizodách. | Všechny podcasty; nejnovější soubor podle data úpravy. |
| **Red Circle – browser extrakce** | Kalendářní měsíční stažení po epizodách. | Aktuální zdroj pro `MKP Studio - Red Circle měsíčně.csv` (krok 6). Oficiální CSV to neumí. |

---

## Postup aktualizace (krok za krokem)

### A – Lifetime součty

**1. Red Circle – lifetime report**  
Report pro **všechny podcasty**, co nejširší rozsah → `EpisodePerformanceReport_*.csv`.

**2. YouTube Studio – tabulka**  
Uložený pohled v Analytics, **doplň nové pořady**, export **„Data v tabulce.csv“**.

**3. Uložení do `data/`**  
Zkopíruj soubory z kroků 1–2 do `data/`.  
⚠️ **Nevkládej** do `data/` nový **Data v grafu.csv**, pokud nechceš riskovat záměnu měsíčních dat (skript ho stejně pro měsíční CSV nepoužije, pokud už máte browser extrakci).

**4. Spuštění skriptu**

```bash
cd ~/Cursor\ Workspace/MKP/Studio
python3 scripts/update_all.py
```

(pouze lifetime: `python3 combine_usage_data.py`)

Přepíše **`MKP Studio - statistika.csv`**.  
**Nepřepisuje** `MKP Studio - Red Circle měsíčně.csv` ani (při existující browser extrakci) `MKP Studio - YouTube měsíčně.csv`.

---

### B – Měsíční rozpad (browser)

Potřebné pro **ROI v čase**, **trend využití** a **měsíční top epizod**. Ideálně **při každé aktualizaci** spolu s A.

**5. Red Circle – měsíční rozpad**

Oficiální CSV **nemá** kalendářní měsíce po epizodách. Postup (ověřený v srpnu 2026):

1. V Red Circle: **Stats → Episode Performance** (ne „Since Published“ — to je relativní pohled, ne kalendářní měsíce).
2. **Select Date Range → All time**, interval **Month**.
3. Po načtení stránky vytáhni měsíční řady z **Redux stavu** aplikace (klíč typu `Episode-Performance-All Podcasts-…-Month`) nebo z interního API (`/api/stats/downloads` s `bucketTerms=download.episodeUUID`).
4. Ulož jako **`data/MKP Studio - Red Circle měsíčně.csv`** (přepiš předchozí).

**Sloupce:** `PodcastName`, `Epizoda`, `EpisodeUUID`, `Měsíc`, `RedCircle_Downloads`, `PodcastUUID` (`Měsíc` = `YYYY-MM`).

Prakticky: DevTools Console → vložit **`scripts/rc_monthly_browser_extract.js`** → stáhnout CSV do `data/`.

**6. YouTube – měsíční rozpad**

Export **Data v grafu** nestačí (viz výše). Postup (ověřený v srpnu 2026):

1. YouTube Studio → **Analytics → rozšířený režim**, stejný filtr pořadů jako u tabulky, rozpad **po měsících**.
2. DevTools Console → **`scripts/yt_monthly_browser_extract.js`** (2×: nejdřív DESC, pak ASC stránka).
   - Skript tahá data z `timelineChartSpec` (dávky po 5 videích, ~50+50 v UI),
   - stáhne `yt_monthly_desc_raw.json` + `yt_monthly_asc_raw.json` do `data/`.
3. **`python3 scripts/update_all.py`** sestaví **`MKP Studio - YouTube měsíčně.csv`** a **`statistiky_meta.json`**.
   - u videí mimo top 50+50: **fallback** — lifetime zhlédnutí → **měsíc publikace** (z `Data v tabulce`).

**Sloupce výstupního CSV:** `Epizoda`, `Měsíc`, `YouTube_Zhlédnutí`, `PodcastName` (`Měsíc` = `YYYY-MM`).

**Kontrola kvality YouTube měsíčního souboru**

| Metrika | Očekávání (řádově) | Varování |
| --- | --- | --- |
| Unikátních epizod | ~160+ | Pod ~20 = pravděpodobně jen graf export (~5 videí) |
| Řádků | stovky | Desítky |
| `statistiky_meta.json` → `zdroj` | obsahuje `browser_extract` | `youtube_mesicne_po_exportu` = přepsáno z grafu |

---

**7. Kontrola výstupů**

Spusťte **`python3 scripts/update_all.py`** — vypíše souhrn. Ručně ve `data/` ověř:

- `MKP Studio - statistika.csv` — nové epizody / vyšší součty
- `MKP Studio - YouTube měsíčně.csv` — ~160+ epizod, poslední měsíc aktuální
- `MKP Studio - Red Circle měsíčně.csv` — stejný poslední měsíc
- `statistiky_meta.json` — `posledni_mesic_statistik` odpovídá

**8. Streamlit**  
Obnov stránku (F5) nebo `./run_media_analytics.sh`.

**9. Git (volitelně)**  
Commit + push změn ve `data/` a dokumentaci.

---

## První spuštění (shrnutí)

**Lifetime (skript):**

- YouTube: `Data v tabulce.csv`
- Red Circle: `EpisodePerformanceReport_*.csv`
- → `python3 combine_usage_data.py`

**Měsíční (browser, nutné pro časové grafy):**

- `MKP Studio - YouTube měsíčně.csv` + `statistiky_meta.json`
- `MKP Studio - Red Circle měsíčně.csv`

Detailní postup: kroky 5–6 výše.

---

## Výstup `combine_usage_data.py`

Soubor **`MKP Studio - statistika.csv`**:

- `PodcastName`, `Epizoda`, `Datum_publikování`
- `YouTube_Zhlédnutí`, `RedCircle_Downloads`, `Celkové_využití`

---

## Automatické vyhledávání souborů

Skript ve `data/` hledá:

- YouTube: `*tabulce*.csv`, volitelně `*grafu*.csv` (graf jen pro doplnění součtů u videí mimo graf, **ne pro přepsání browser měsíčního CSV**)
- Red Circle: nejnovější `EpisodePerformanceReport_*.csv`

---

## Tipy

- **Měsíční data = browser**, lifetime = CSV + skript. Nemíchat postupy.
- Po `combine_usage_data.py` zkontroluj, že `YouTube měsíčně.csv` **nemá méně epizod** než před během.
- Bez aktuálního RC měsíčního souboru: ROI v čase a trend RC použijí fallback (měsíc publikace) nebo stará data.
- Při změně postupu extrakce nebo datového modelu **aktualizuj tento návod a `README_STREAMLIT.md`** (viz pravidlo v `.cursor/rules/`).
