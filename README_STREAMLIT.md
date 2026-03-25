# Analýza online obsahu - Streamlit aplikace

Interaktivní webová aplikace pro analýzu a vizualizaci dat o využití online obsahu (podcasty z RedCircle a videa z YouTube).

## 📋 Požadavky

Aplikace vyžaduje následující Python balíčky:
- `streamlit` - webový framework
- `pandas` - práce s daty
- `altair` - vytváření grafů

### Instalace závislostí

Pokud ještě nemáte nainstalované potřebné balíčky, nainstalujte je pomocí:

```bash
pip3 install streamlit pandas altair openpyxl
```

Nebo pokud používáte `pip`:

```bash
pip install streamlit pandas altair openpyxl
```

## 🚀 Spuštění aplikace

### Metoda 1: Přes Streamlit (doporučeno)

Nejjednodušší způsob, jak spustit aplikaci:

```bash
python3 -m streamlit run streamlit_media_analytics.py
```

Aplikace se automaticky otevře v prohlížeči na adrese `http://localhost:8501`.

### Metoda 2: Přes shell skript

Pokud máte vytvořený shell skript `run_media_analytics.sh`:

```bash
./run_media_analytics.sh
```

**Poznámka:** Ujistěte se, že má skript spustitelná práva:
```bash
chmod +x run_media_analytics.sh
```

## 📁 Požadované soubory

Aplikace načítá soubor **`data/MKP Studio - statistika.csv`** (složka **`data/`** vedle skriptu `streamlit_media_analytics.py`). Volitelně **`data/MKP Studio - YouTube měsíčně.csv`** pro trend po měsících.

### Struktura CSV souboru

Soubor musí obsahovat následující sloupce:
- `PodcastName` - název podcastu/pořadu
- `Epizoda` - název epizody
- `Datum_publikování` - datum publikace (formát: YYYY-MM-DD)
- `YouTube_Zhlédnutí` - počet zhlédnutí na YouTube
- `RedCircle_Downloads` - počet stažení z RedCircle
- `Celkové_využití` - celkový součet využití

## 🎯 Funkce aplikace

### Přehledové metriky
- Počet epizod
- Celkem stažení (RedCircle)
- Celkem zhlédnutí (YouTube)
- Celkové využití

### Filtry
- **Podcast / pořad** - výběr konkrétních podcastů
- **Období publikace** - výběr časového rozsahu

### Grafy a vizualizace
1. **Top epizody podle celkového využití** - sloupcový graf s nejúspěšnějšími epizodami
2. **Vztah mezi staženími a zhlédnutími** - scatter plot ukazující korelaci mezi platformami
3. **Trend využití v čase** - časová řada s možností agregace po týdnech nebo měsících
4. **Podíl využití podle platformy** - koláčový graf rozdělení mezi podcasty a YouTube

### Analytické vhledy
- TOP 5 nejsilnějších epizod
- Rozdělení využití podle platformy (s koláčovým grafem)
- Výkon podle podcastu/pořadu - souhrnná tabulka

## 🛠️ Řešení problémů

### Chyba: "command not found: streamlit"

Pokud se vám zobrazí tato chyba, použijte:
```bash
python3 -m streamlit run streamlit_media_analytics.py
```

Místo:
```bash
streamlit run streamlit_media_analytics.py
```

### Chyba: "No module named 'streamlit'"

Nainstalujte Streamlit:
```bash
pip3 install streamlit
```

### Soubor CSV nebyl nalezen

Ujistěte se, že:
1. Existuje složka **`data/`** v kořeni projektu (vedle `streamlit_media_analytics.py`).
2. Uvnitř je soubor **`MKP Studio - statistika.csv`** (vygeneruje ho `combine_usage_data.py`).
3. Název souboru je přesně `MKP Studio - statistika.csv` (včetně mezer a velkých písmen).

### Aplikace se nespustí při přímém spuštění Python skriptu

Aplikace **musí** být spuštěna přes Streamlit. Použijte:
```bash
python3 -m streamlit run streamlit_media_analytics.py
```

Přímé spuštění `python3 streamlit_media_analytics.py` nefunguje, protože Streamlit vyžaduje svůj vlastní runtime.

## 📊 Tipy pro použití

1. **Filtrování dat** - Použijte filtry v levém bočním panelu pro zobrazení konkrétních podcastů nebo časových období
2. **Interaktivní grafy** - Všechny grafy jsou interaktivní - najetím myši zobrazíte detailní informace
3. **Export dat** - Data můžete exportovat přímo z tabulek v aplikaci (tlačítko "Download" v pravém horním rohu tabulky)

## 🔄 Aktualizace dat

Pro aktualizaci dat použijte skript `combine_usage_data.py`, který zapisuje výstupy do složky **`data/`** (např. `data/MKP Studio - statistika.csv`). Po vytvoření nového souboru stačí obnovit stránku v prohlížeči (F5), aby se načetla nová data.

## 📝 Poznámky

- Aplikace automaticky cachuje načtená data pro rychlejší načítání při opakovaném použití
- Všechny grafy jsou responzivní a přizpůsobí se velikosti okna
- Data se načítají při každém spuštění aplikace, takže změny v CSV souboru budou viditelné po obnovení stránky

