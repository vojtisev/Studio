# Návod pro aktualizaci statistik podcastů

## Co skript dělá
Kombinuje data z YouTube Studio a Red Circle do jednoho přehledného souboru s celkovým využitím epizod.

## Princip práce s časovým obdobím (aktuální nastavení)

Na **obou platformách** při exportu vycházím z časového rozsahu v podstatě **„od začátku věků“** – tedy **od nejdřívějšího data, které daná analytika nabízí**, až po aktuální stav. Důvod: **pracuji vždy jen s jedním aktuálním souborem** od každé platformy; neskládám historii z více exportů za sebou.

- **YouTube Studio:** exportuji data s **pohledem po měsících** (měsíční rozpad ve „Data v grafu“). U **tabulky** používám **předem připravený pohled / uložený filtr** v Analytics – do něj při každé aktualizaci **doplním nové pořady od posledního exportu** (objeví se **nahoře** v seznamu), takže mám přehled o tom, co přibylo.
- **Red Circle:** při generování reportu volím **všechny podcasty** (celý rozsah pořadů relevantních pro přehled).

Skript sám **nepřepisuje období** – bere vždy obsah posledních stažených CSV ve složce `data/`.

## Kam ukládat soubory (po přesunu projektu)
**Vstupní exporty** (YouTube, Red Circle) ukládej do podsložky **`data/`** uvnitř projektu:

**`~/Cursor Workspace/MKP/Studio/data/`**

Skripty (`combine_usage_data.py`, `streamlit_media_analytics.py`) zůstávají v kořeni projektu (`Studio/`). **Výstupní soubory** (`MKP Studio - statistika.csv`, případně `MKP Studio - YouTube měsíčně.csv`) skript zapisuje také do **`data/`**.

Starší exporty můžeš v `data/` nechávat – u více souborů stejného typu skript bere **nejnovější podle data úpravy souboru** (kromě výstupů, které se při běhu přepisují).

> Skript nepotřebuje běžet z konkrétní složky – cesty si bere sám od souboru `combine_usage_data.py`. Stačí: `python3 combine_usage_data.py` z adresáře `Studio/`, nebo plná cesta ke skriptu.

## Období – technický význam pro skript
Skript **nesestavuje vlastní časové období**; bere vždy to, co je uvnitř stažených souborů.

| Zdroj | Co v exportu obvykle je | Poznámka |
|--------|---------------------------|----------|
| **YouTube – Data v tabulce** | Celková zhlédnutí na video v rozsahu, který export zahrnuje (u nás typicky plná historie kanálu / max. rozsah). | Filtr v uloženém pohledu doplňuj o nové pořady po každém exportu. |
| **YouTube – Data v grafu** | Měsíční rozpad zhlédnutí – skript je sečte po epizodách a použije pro součty + soubor `MKP Studio - YouTube měsíčně.csv`. | Export s měsíčním pohledem. |
| **Red Circle – EpisodePerformanceReport** | V názvu souboru je období reportu; uvnitř jsou aktuální údaje podle nastavení exportu. | Volba **všech podcastů**; ve složce může být více souborů – skript vezme **nejnovější podle data úpravy** souboru na disku. |

## Postup aktualizace dat (krok za krokem)

1. **Red Circle**  
   Vygeneruj report pro **všechny podcasty**, v co nejširším časovém rozsahu (od nejdřívějšího možného data po současnost), stáhni CSV `EpisodePerformanceReport_*.csv`.

2. **YouTube Studio – tabulka**  
   Otevři **předem připravený pohled** (uložený filtr) v Analytics. **Doplň do filtru nové pořady**, které přibyly od minulého exportu (typicky **nahoře** v seznamu). Exportuj **„Data v tabulce.csv“** (plný rozsah dle nastavení pohledu).

3. **YouTube Studio – graf (měsíčně)**  
   Nastav export s **pohledem po měsících** a stáhni **„Data v grafu.csv“**.

4. **Uložení do projektu**  
   Zkopíruj stažené soubory do **`~/Cursor Workspace/MKP/Studio/data/`** (případně přepiš předchozí stejné názvy).

5. **Spuštění skriptu**  
   V terminálu z kořene projektu:
   ```bash
   cd ~/Cursor\ Workspace/MKP/Studio
   python3 combine_usage_data.py
   ```

6. **Kontrola výstupů**  
   Ve složce `data/` se přepíší mimo jiné **`MKP Studio - statistika.csv`** a **`MKP Studio - YouTube měsíčně.csv`**.

7. **Streamlit (lokálně nebo po pushi v cloudu)**  
   Obnov stránku aplikace (F5), případně znovu nasaď / počkej na rebuild na Streamlit Cloud.

8. **Git (volitelně)**  
   Pokud verzuješ data v repozitáři: v GitHub Desktopu **commit + push** změn ve složce `data/` a souvisejících souborech.

## Jak připravit data pro první spuštění (shrnutí)

### Soubory z analytik
**YouTube Studio:**
- **"Data v tabulce.csv"**
- Volitelně doporučeno: **"Data v grafu.csv"** (měsíční rozpad)

**Red Circle:**
- **"EpisodePerformanceReport_*.csv"**

### Uložení a příkaz
Exporty ulož do **`~/Cursor Workspace/MKP/Studio/data/`**, pak:

```bash
cd ~/Cursor\ Workspace/MKP/Studio
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
- Starší soubory ve `data/` můžeš nechat – skript použije nejnovější vstupy podle typu.
- Bez **„Data v grafu.csv“** skript použije pro YouTube součty jen z tabulky; měsíční trend v aplikaci pak nemusí být k dispozici.
