# Analýza online obsahu (Streamlit)

---

## 1. Základní informace

**Co aplikace je:** Jednoduchý webový přehled (dashboard) nad sloučenými daty z **Red Circle** (stažení podcastů) a **YouTube** (zhlédnutí videí). Data se berou z CSV souborů vygenerovaných skriptem `combine_usage_data.py`.

**K čemu slouží:** Rychlý přehled využití obsahu podle epizod a pořadů, srovnání platforem, základní grafy a orientační **odhad návratnosti (ROI)** vůči **nákladům po rocích** (tabulka), **ochotě platit (WTP)** za jedno využití (stažení nebo zhlédnutí) a nově i **kumulativnímu vývoji ROI v čase**.

**Kdo je „uživatel“ v tomto dokumentu:** kdokoli, kdo si dashboard jen prohlíží (sekce 2), a správce, který aplikaci spouští nebo nasazuje (sekce 3).

---

## 2. Informace pro uživatele dashboardu

### 2.1 Levý panel – filtry

- **Pořad:** Výběr jednoho nebo více pořadů. Epizody bez přiřazeného pořadu se zobrazují jako **„Bez pořadu“**. Ve výchozím stavu jsou vybraná všechna pořady (celkový přehled).

### 2.2 Horní přehled – čísla (metriky)


| Ukazatel                       | Co znamená                                                                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Počet epizod**               | Kolik epizod (řádků) zůstane v přehledu po zúžení filtrem pořadu.                                                                                      |
| **Celkem — Stažení**         | Součet **stažení** ze všech zobrazených epizod (Red Circle).                                                                                           |
| **Celkem — Zhlédnutí**       | Součet **zhlédnutí** ze všech zobrazených epizod (YouTube).                                                                                            |
| **Celkové využití**          | **Stažení + zhlédnutí** dohromady: jedna jednotka = jedno stažení **nebo** jedno zhlédnutí (jedna osoba může obojí, počítají se obě platformy zvlášť). |


U každé metriky je v aplikaci **nápověda** (ikona „?“ u hodnoty) se stejným vysvětlením.

### 2.3 ROI – odhad návratnosti

Pod přehledem je **jeden odhad ROI** podle **ochoty platit (WTP)** za jednotku využití (jedno stažení nebo jedno zhlédnutí):

- **WTP: 37 Kč na využití** – hodnota z [dotazníkového šetření VISK 2024](https://www.hodnota-knihovny.cz/wp-content/uploads/2025/01/infografika_audioknihy_2024_visk.pdf) (infografika audioknihy).

**Náklady ve jmenovateli** nejsou jedna pevná částka, ale součet z `**data/naklady.csv`**:

- za každý **dřívější kalendářní rok** než rok „posledního měsíce statistik“ se započítá **celá** roční částka z tabulky;
- za **ten rok**, ve kterém leží poslední měsíc ve statistikách, se započítá poměr **`(M − 1) / 12`**, kde **M** je číslo posledního měsíce v exportu (např. poslední měsíc **březen → M = 3** → náklady za **2** měsíce roku, tj. **2/12**; kompenzuje to situaci, kdy kalendář už pokročil o měsíc dál než kompletní statistiky).

**Poslední měsíc statistik** se bere z měsíčního exportu: soubor `**data/MKP Studio - YouTube měsíčně.csv`** (nejvyšší `Měsíc` ve formátu `YYYY-MM`), případně ze `**data/statistiky_meta.json**`, který při exportu zapisuje `combine_usage_data.py`.

**Vzorec ROI:**

`ROI = ((počet využití ve výběru × 37 Kč) − alokované náklady) ÷ alokované náklady`

kde **celkové náklady** organizace = výše popsaný součet z `naklady.csv` s poměrem **`(M−1)/12`** za běžící rok (**M** = poslední měsíc ve statistikách), a **alokované náklady** = celkové náklady × (**počet epizod ve filtru** ÷ **počet epizod v celém** statistickém souboru). Při výběru všech pořadů je podíl 100 % — ROI odpovídá celému portfoliu. (Alokace podle *podílu využití* by při stejném Kč/využití dávala pro každý neprázdný výběr stejné procento ROI; proto používáme podíl podle **počtu dílů**, aby se ROI mezi pořady lišilo podle toho, kolik využití připadá na „jeden díl“ výběru.)

**Jak číst výsledek:**


| ROI           | Význam                                                                      |
| ------------- | --------------------------------------------------------------------------- |
| **0 %**       | Přínos z využití je **rovny** použitým nákladům (v tomto modelu „na nule“). |
| **Kladné %**  | Přínos **přesahuje** náklady.                                               |
| **Záporné %** | Náklady **nejsou** hodnotou využití pokryté.                                |


V aplikaci je u ROI **stručný popisek** (včetně poměru epizod, alokovaných Kč a odkazu na šetření) a rozbalovací **Rozpis nákladů**. Graf porovnává **hodnotu využití** (využití × 37 Kč) s **alokovanými náklady**. **Využití** v čitateli odpovídá **aktuálnímu filtru**; **náklady** v jmenovateli jsou **poměřené podle počtu epizod** ve výběru vůči celému souboru. Časová vazba nákladů na poslední měsíc ve statistikách zůstává – jde o orientační model, ne o účetní závěrku.

#### ROI v čase

Pod základní ROI metrikou je také **graf kumulativního ROI v čase**. Jeho smyslem je ukázat, jak se vybraný pilot nebo vybraný pořad postupně přibližuje k cíli **0 % ROI**, tedy k bodu, kdy odhadovaný přínos **dorovná** alokované náklady (návratnost nákladů). Cokoliv nad 0 % je přínos nad náklady; pod 0 % znamená, že náklady ještě nejsou pokryté.

Graf používá **stejný model jako statické ROI**:

- **WTP** zůstává **37 Kč / využití**
- **alokace nákladů** zůstává podle **podílu epizod ve filtru** vůči celému souboru
- **náklady v čase** se počítají stejnou prorací podle posledního měsíce

Po měsících se počítá:

`ROI_kumul(M) = ((kumulativní využití do měsíce M × 37 Kč) − alokované náklady do měsíce M) ÷ alokované náklady do měsíce M`

##### Jak vzniká kumulativní využití

- **YouTube**: skutečná měsíční data ze souboru `**data/MKP Studio - YouTube měsíčně.csv`**.
- **Red Circle**: skutečná měsíční data ze souboru `**data/MKP Studio - Red Circle měsíčně.csv`** (kalendářní měsíce z Episode Performance / API). Pokud tento soubor chybí, aplikace dočasně přiřadí lifetime stažení epizody k měsíci její publikace.

Na **posledním měsíci statistik** by kumulativní ROI mělo odpovídat souhrnnému ROI pro stejný filtr (stejné WTP, stejná alokace nákladů).

##### Jak se do toho promítá filtr pořadu

Stejně jako u statické metriky se i graf ROI v čase vždy vztahuje k **aktuálnímu výběru pořadů**:

- při výběru všech pořadů ukazuje křivku pro celé portfolio,
- při výběru jednoho pořadu ukazuje vývoj ROI jen pro tento pořad,
- ale náklady nejsou „skutečné náklady pořadu“; jde o **poměrně alokovaný podíl** celkových nákladů podle počtu epizod ve výběru.

Graf proto neslouží jako účetní evidence po měsících, ale jako **manažerský a orientační pohled na vývoj návratnosti** v čase při zachování stejného modelu, který používá hlavní ROI metrika.

Čísla se **mění podle filtru pořadu** – ukazují vždy jen vybrané pořady.

### 2.4 Grafy a další části stránky

1. **Top epizody podle celkového využití** – Sloupcový graf nejúspěšnějších epizod (stažení + zhlédnutí). Posuvník mění počet epizod v žebříčku.
2. **Vztah mezi staženími a zhlédnutími** – Scatter graf: osy = stažení vs. zhlédnutí, bubliny velikost podle celkového využití; barva = pořad.
3. **Trend využití v čase** – Měsíční součty **YouTube zhlédnutí** a **Red Circle stažení** (dvě křivky). Defaultně jen měsíce s nenulovým využitím; volitelně i nuly.
4. **Rozdělení celkového využití podle zdroje** – Koláč s popisem zdroje: **Red Circle (stažení)** vs. **YouTube (zhlédnutí)**.
5. **Pareto: kolik epizod pokryje využití** – kumulativní podíl celkového využití podle pořadí epizod.
6. **Měsíční top epizoda (YouTube)** – výběr měsíce a zobrazení epizod s nejvyššími zhlédnutími v daném měsíci.
7. **Analytické vhledy a vyhledávání** – Tabulky TOP epizod a TOP pořadů. V sidebaru lze vyhledat konkrétní pořad nebo epizodu/díl podle textu.

Grafy jsou interaktivní (tooltip po najetí myší). U tabulek lze v rozhraní Streamlit často data zkopírovat nebo stáhnout (záleží na verzi prohlížeče a Streamlitu).

---

## 3. Technické informace (spuštění, data, řešení problémů)

### 3.1 Požadavky

Python balíčky jsou uvedeny v `**requirements.txt`** (mimo jiné `streamlit`, `pandas`, `altair`, `numpy`). Instalace např.:

```bash
pip3 install -r requirements.txt
```

### 3.2 Spuštění lokálně

Z kořene projektu (složka se `streamlit_media_analytics.py`):

```bash
python3 -m streamlit run streamlit_media_analytics.py
```

Nebo skript `./run_media_analytics.sh` (musí být spustitelný: `chmod +x run_media_analytics.sh`).

Aplikace běží typicky na `http://localhost:8501`.

**Poznámka:** Aplikaci je nutné spouštět přes Streamlit (`streamlit run`), ne přímo `python3 streamlit_media_analytics.py` bez runtime Streamlitu.

### 3.3 Datové soubory


| Soubor                                      | Účel                                                                                                                                                     |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `**data/MKP Studio - statistika.csv`**      | Hlavní přehled epizod (generuje `combine_usage_data.py`).                                                                                                |
| `**data/MKP Studio - YouTube měsíčně.csv**` | Měsíční zhlédnutí + určení **posledního měsíce** pro náklady a trend.                                                                                    |
| `**data/MKP Studio - Red Circle měsíčně.csv**` | Měsíční stažení po epizodách (kalendářní měsíce); používá ROI v čase a trend využití. Ruční / jednorázový export z Red Circle.                         |
| `**data/naklady.csv`**                      | Sloupce `**rok**`, `**naklady_Kc**` – roční náklady (minulé uzavřené roky celé částky; u běžícího roku plán za 12 měsíců, v ROI se krátí poměrem M/12).  |
| `**data/statistiky_meta.json**`             | Volitelná kopie **posledního měsíce** (`posledni_mesic_statistik`, formát `YYYY-MM`); zapisuje se při běhu `combine_usage_data.py` spolu s měsíčním CSV. |


Struktura hlavního statistického CSV: sloupce `PodcastName`, `Epizoda`, `Datum_publikování`, `YouTube_Zhlédnutí`, `RedCircle_Downloads`, `Celkové_využití` (podrobnosti v `**Jak na aktualizaci statistiky podcastů.md`**).

**Příklad `naklady.csv`:**

```csv
rok,naklady_Kc
2023,30000
2024,200000
2025,800000
2026,800000
```

### 3.4 Aktualizace dat

Spusťte z kořene projektu:

```bash
python3 combine_usage_data.py
```

Výstupy se zapíší do `**data/**` (včetně měsíčního CSV a `statistiky_meta.json`, pokud je k dispozici export **Data v grafu.csv**). V prohlížeči obnovte stránku (F5). Podrobný postup exportů z YouTube a Red Circle je v `**Jak na aktualizaci statistiky podcastů.md`**.

### 3.5 Řešení problémů


| Problém                        | Postup                                                                                                                      |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `command not found: streamlit` | Použijte `python3 -m streamlit run streamlit_media_analytics.py`                                                            |
| `No module named 'streamlit'`  | `pip3 install streamlit` nebo `pip3 install -r requirements.txt`                                                            |
| CSV nebyl nalezen              | Zkontrolujte existenci složky `**data/**` a souboru `**MKP Studio - statistika.csv**` přesně s tímto názvem (včetně mezer). |
| ROI se nezobrazí               | Doplňte `**data/naklady.csv**` a měsíční export (spusťte `combine_usage_data.py` s **Data v grafu.csv**).                   |
| Prázdná nebo stará data        | Znovu spusťte `combine_usage_data.py` a obnovte stránku.                                                                    |


### 3.6 Poznámky k chování aplikace

- Načtená data jsou v Streamlitu **cachovaná** – po změně CSV může být potřeba obnovit stránku nebo v menu „Rerun“.
- ROI a všechny součty respektují **aktuální výběr v levém filtru**.

---

*Projekt: MKP Studio – analýza online obsahu (Red Circle + YouTube).*