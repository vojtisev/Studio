import json
import math
import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from typing import Dict, Optional, Tuple
import csv
from pandas.errors import ParserError


# CSV ve složce data/ vedle skriptu
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "MKP Studio - statistika.csv"
MONTHLY_CSV_PATH = DATA_DIR / "MKP Studio - YouTube měsíčně.csv"
MONTHLY_RC_CSV_PATH = DATA_DIR / "MKP Studio - Red Circle měsíčně.csv"
NAKLADY_CSV_PATH = DATA_DIR / "naklady.csv"
META_JSON_PATH = DATA_DIR / "statistiky_meta.json"

# Jednotné popisky metrik v UI: Stažení, Zhlédnutí, Celkové využití (vnitřně zůstávají anglické názvy sloupců z DataFrame)
L_POŘAD = "Pořad"
# 2. pád pro nadpisy typu „podle Pořadu“ (ne .lower() z „Pořad“ → „pořad“)
L_POŘADU = "Pořadu"
L_EPIZODA = "Epizoda"
L_STAŽENÍ = "Stažení"
L_ZHLÉDNUTÍ = "Zhlédnutí"
# Metrika + zdroj dat (pro nadpisy/koláč; základ zůstává v L_STAŽENÍ / L_ZHLÉDNUTÍ)
L_STAŽENÍ_RC_POPIS = f"{L_STAŽENÍ} (Red Circle)"
L_ZHLÉDNUTÍ_YT_POPIS = f"{L_ZHLÉDNUTÍ} (YouTube)"
L_CELKEM_VYUŽITÍ = "Celkové využití"
# 2. pád: „podle celkového využití“, „rozdělení celkového využití“, „z celkového využití“
L_CELKEM_VYUŽITÍ_GEN = "celkového využití"

# Ochota platit (WTP) za jednotku využití – z dotazníkového šetření VISK 2024
WTP_CZK = 37
WTP_SURVEY_URL = (
    "https://www.hodnota-knihovny.cz/wp-content/uploads/2025/01/infografika_audioknihy_2024_visk.pdf"
)

# Oddělovač tisíců mezerou (CZ); Altair/D3 locale pro tooltipy a osy
_CZ_NUMBER_LOCALE = {
    "decimal": ",",
    "thousands": " ",
    "grouping": [3],
    "currency": ["", " Kč"],
}

_CZ_MONTHS = (
    "leden",
    "únor",
    "březen",
    "duben",
    "květen",
    "červen",
    "červenec",
    "srpen",
    "září",
    "říjen",
    "listopad",
    "prosinec",
)


def format_mesic_cz(ts) -> str:
    """Český popisek měsíce pro tooltips (např. „srpen 2026“)."""
    try:
        t = pd.Timestamp(ts)
        if pd.isna(t):
            return ""
        return f"{_CZ_MONTHS[int(t.month) - 1]} {int(t.year)}"
    except (ValueError, TypeError, OverflowError, IndexError):
        return str(ts)


def with_mesic_popis(df: pd.DataFrame, col: str = "Měsíc") -> pd.DataFrame:
    """Přidá sloupec Měsíc_popis s českým názvem měsíce pro tooltips."""
    out = df.copy()
    if col in out.columns:
        out["Měsíc_popis"] = out[col].map(format_mesic_cz)
    return out


def fmt_tisice(n: object) -> str:
    """Čísla bez desetinných míst, tisíce oddělené mezerou (ne čárkou jako v en_US)."""
    try:
        x = float(n)
        if math.isnan(x) or math.isinf(x):
            return str(n)
        return f"{x:,.0f}".replace(",", " ")
    except (ValueError, TypeError, OverflowError):
        return str(n)


def alt_cz(chart: alt.Chart) -> alt.Chart:
    """Nastaví locale pro formátování čísel v grafech (tooltipy, osy)."""
    return chart.configure(locale={"number": _CZ_NUMBER_LOCALE})


def dataframe_display_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Přejmenuje sloupce pro zobrazení v tabulkách (konzistentní české názvy)
    a formátuje čísla s oddělovačem tisíců mezerou (např. 1 000)."""
    mapping = {
        "EpisodeName": L_EPIZODA,
        "PodcastName": L_POŘAD,
        "Downloads": L_STAŽENÍ,
        "Zhlédnutí": L_ZHLÉDNUTÍ,
        "TotalUsage": L_CELKEM_VYUŽITÍ,
    }
    out = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    out = out.reset_index(drop=True)
    out.index = pd.RangeIndex(1, len(out) + 1, name="Pořadí")
    for col in out.select_dtypes(include="number").columns:
        out[col] = out[col].map(fmt_tisice)
    return out


def load_naklady_dict() -> Dict[int, float]:
    if not NAKLADY_CSV_PATH.exists():
        return {}
    df = pd.read_csv(NAKLADY_CSV_PATH)
    col_y = "rok" if "rok" in df.columns else df.columns[0]
    col_c = "naklady_Kc" if "naklady_Kc" in df.columns else df.columns[1]
    out: Dict[int, float] = {}
    for _, row in df.iterrows():
        try:
            y = int(row[col_y])
            out[y] = float(row[col_c])
        except (ValueError, TypeError):
            continue
    return out


def resolve_stats_end_year_month() -> Optional[Tuple[int, int]]:
    """Poslední kalendářní měsíc pokrytý statistikami (rok, měsíc 1–12)."""
    if MONTHLY_CSV_PATH.exists():
        df = pd.read_csv(MONTHLY_CSV_PATH)
        if len(df) and "Měsíc" in df.columns:
            mxs = df["Měsíc"].astype(str).str.strip()
            mx = mxs.max()
            if mx and len(mx) >= 7:
                ts = pd.Timestamp(mx + "-01")
                return (int(ts.year), int(ts.month))
    if META_JSON_PATH.exists():
        try:
            meta = json.loads(META_JSON_PATH.read_text(encoding="utf-8"))
            pm = meta.get("posledni_mesic_statistik")
            if pm:
                s = str(pm).strip()
                ts = pd.Timestamp(s + "-01") if len(s) == 7 and s[4] == "-" else pd.Timestamp(s)
                return (int(ts.year), int(ts.month))
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return None


def _proration_months_for_year(end_m: int) -> int:
    """Počet měsíců pro poměr běžícího roku: poslední měsíc ve statistikách mínus 1 (např. březen=3 → 2 měsíce)."""
    return max(0, int(end_m) - 1)


def total_cost_prorated(naklady: Dict[int, float], end_y: int, end_m: int) -> float:
    """Plné roky před end_y + poměr roku end_y: (M−1)/12, kde M je měsíc posledních statistik."""
    pm = _proration_months_for_year(end_m)
    total = 0.0
    for y in sorted(naklady.keys()):
        if y < end_y:
            total += naklady[y]
        elif y == end_y:
            total += naklady[y] * (pm / 12.0)
    return total


def cost_breakdown_lines(naklady: Dict[int, float], end_y: int, end_m: int) -> str:
    """Krátký textový rozpis pro nápovědu / expander."""
    pm = _proration_months_for_year(end_m)
    parts = []
    for y in sorted(naklady.keys()):
        if y < end_y:
            parts.append(f"{y}: {fmt_tisice(naklady[y])} Kč (celý rok)")
        elif y == end_y:
            p = naklady[y] * (pm / 12.0)
            parts.append(f"{y}: {fmt_tisice(naklady[y])} × ({end_m}−1)/12 = {fmt_tisice(p)} Kč")
    return " · ".join(parts) if parts else ""


def build_cumulative_roi_series(
    df: pd.DataFrame,
    df_all: pd.DataFrame,
    monthly_yt: Optional[pd.DataFrame],
    monthly_rc: Optional[pd.DataFrame],
    naklady: Dict[int, float],
    end_y: int,
    end_m: int,
) -> pd.DataFrame:
    """Kumulativní ROI po měsících (stejný model jako statické ROI).

    YouTube i Red Circle berou skutečná měsíční data (pokud jsou k dispozici).
    Když chybí RC měsíční export, fallback: lifetime Downloads → měsíc PublishDate.
    """
    empty = pd.DataFrame(columns=["Měsíc", "Využití kumul", "Hodnota kumul", "Náklady alok", "ROI"])
    n_all = len(df_all)
    n_sel = len(df)
    if n_all <= 0 or n_sel <= 0 or not naklady:
        return empty

    share_episodes = n_sel / n_all
    end_ts = pd.Timestamp(year=end_y, month=end_m, day=1)
    episodes_in_scope = set(df["EpisodeName"])

    # Red Circle měsíčně (preferováno) / fallback na měsíc publikace
    rc_by_month = pd.DataFrame(columns=["Měsíc", "rc_month_usage"])
    if monthly_rc is not None and len(monthly_rc) > 0:
        m_rc = monthly_rc[monthly_rc["Epizoda"].isin(episodes_in_scope)].copy()
        if len(m_rc) > 0:
            rc_by_month = (
                m_rc.groupby("Měsíc", as_index=False)["RedCircle_Downloads"]
                .sum()
                .rename(columns={"RedCircle_Downloads": "rc_month_usage"})
            )
    if rc_by_month.empty:
        rc = df[["EpisodeName", "Downloads", "PublishDate"]].copy()
        rc["Měsíc"] = rc["PublishDate"].dt.to_period("M").dt.to_timestamp()
        rc.loc[rc["Měsíc"].isna(), "Měsíc"] = end_ts
        rc_by_month = (
            rc.groupby("Měsíc", as_index=False)["Downloads"]
            .sum()
            .rename(columns={"Downloads": "rc_month_usage"})
        )

    # YouTube měsíčně pro epizody ve výběru
    yt_by_month = pd.DataFrame(columns=["Měsíc", "yt_month_usage"])
    if monthly_yt is not None and len(monthly_yt) > 0:
        m = monthly_yt[monthly_yt["Epizoda"].isin(episodes_in_scope)].copy()
        if len(m) > 0:
            yt_by_month = (
                m.groupby("Měsíc", as_index=False)["YouTube_Zhlédnutí"]
                .sum()
                .rename(columns={"YouTube_Zhlédnutí": "yt_month_usage"})
            )

    # Začátek řady: nejdřívější z (leden prvního roku nákladů, první RC/YT aktivita)
    start_candidates: list[pd.Timestamp] = []
    if naklady:
        start_candidates.append(pd.Timestamp(year=min(naklady.keys()), month=1, day=1))
    if len(rc_by_month) > 0:
        rc_nz = rc_by_month[rc_by_month["rc_month_usage"] > 0]
        start_candidates.append(
            pd.Timestamp((rc_nz if len(rc_nz) else rc_by_month)["Měsíc"].min())
        )
    if len(yt_by_month) > 0:
        yt_nz = yt_by_month[yt_by_month["yt_month_usage"] > 0]
        start_candidates.append(
            pd.Timestamp((yt_nz if len(yt_nz) else yt_by_month)["Měsíc"].min())
        )
    if not start_candidates:
        return empty
    start_ts = min(start_candidates)
    if start_ts > end_ts:
        return empty

    months = pd.date_range(start=start_ts, end=end_ts, freq="MS")
    series = pd.DataFrame({"Měsíc": months})
    series = series.merge(yt_by_month, on="Měsíc", how="left")
    series = series.merge(rc_by_month, on="Měsíc", how="left")
    series["yt_month_usage"] = series["yt_month_usage"].fillna(0).astype(float)
    series["rc_month_usage"] = series["rc_month_usage"].fillna(0).astype(float)
    series["usage_month"] = series["yt_month_usage"] + series["rc_month_usage"]
    series["Využití kumul"] = series["usage_month"].cumsum()
    series["Hodnota kumul"] = series["Využití kumul"] * WTP_CZK

    costs = []
    for ts in series["Měsíc"]:
        costs.append(total_cost_prorated(naklady, int(ts.year), int(ts.month)) * share_episodes)
    series["Náklady alok"] = costs
    series["ROI"] = series.apply(
        lambda r: (r["Hodnota kumul"] - r["Náklady alok"]) / r["Náklady alok"]
        if r["Náklady alok"] > 0
        else float("nan"),
        axis=1,
    )
    return series[["Měsíc", "Využití kumul", "Hodnota kumul", "Náklady alok", "ROI"]].reset_index(drop=True)


@st.cache_data
def load_data(csv_path: str, csv_mtime: float) -> pd.DataFrame:
    """Načte data z CSV a převede názvy sloupců na standardní formát.

    Pozn.: `csv_mtime` se používá jen pro invalidaci cache při ruční editaci souboru.
    """
    _ = csv_mtime
    try:
        df = pd.read_csv(csv_path)
    except ParserError:
        # Typicky po ruční editaci: čárka v PodcastName/Epizoda bez uvozovek → víc polí v řádku.
        # Opravíme řádky na očekávaný počet sloupců (zachováme posledních 5 polí a „nadbytek“
        # přilepíme zpět k prvnímu sloupci).
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=",", quotechar='"', escapechar="\\")
            rows = list(reader)
        if not rows:
            return pd.DataFrame()

        header = rows[0]
        expected_cols = len(header)
        fixed_rows = [header]

        for row in rows[1:]:
            if len(row) == expected_cols:
                fixed_rows.append(row)
                continue

            if len(row) > expected_cols and expected_cols >= 2:
                # Předpoklad: „navíc“ je jen v prvním textovém sloupci (PodcastName).
                tail_len = expected_cols - 1
                head_parts = row[: len(row) - tail_len]
                tail = row[len(row) - tail_len :]
                fixed_rows.append([",".join(head_parts)] + tail)
                continue

            # Pokud je polí málo, doplníme prázdné (ať načtení nespadne).
            if len(row) < expected_cols:
                fixed_rows.append(row + [""] * (expected_cols - len(row)))
                continue

            # Fallback: ořízneme na očekávaný počet.
            fixed_rows.append(row[:expected_cols])

        df = pd.DataFrame(fixed_rows[1:], columns=fixed_rows[0])

    # Mapování názvů sloupců z nového formátu na standardní
    column_mapping = {
        "Epizoda": "EpisodeName",
        "Datum_publikování": "PublishDate",
        "YouTube_Zhlédnutí": "Zhlédnutí",
        "RedCircle_Downloads": "Downloads",
        "Celkové_využití": "TotalUsage",
    }
    
    # Přejmenování sloupců
    df = df.rename(columns=column_mapping)

    # zajištění správných typů
    if "PublishDate" in df.columns:
        df["PublishDate"] = pd.to_datetime(df["PublishDate"], errors="coerce")
    if "Downloads" in df.columns:
        df["Downloads"] = pd.to_numeric(df["Downloads"], errors="coerce").fillna(0).astype(int)
    else:
        df["Downloads"] = 0
    if "Zhlédnutí" in df.columns:
        df["Zhlédnutí"] = pd.to_numeric(df["Zhlédnutí"], errors="coerce").fillna(0).astype(int)
    else:
        df["Zhlédnutí"] = 0

    if "TotalUsage" in df.columns:
        df["TotalUsage"] = pd.to_numeric(df["TotalUsage"], errors="coerce").fillna(0).astype(int)
    else:
        df["TotalUsage"] = (df["Downloads"] + df["Zhlédnutí"]).astype(int)

    # normalizace názvů pořadů – epizody bez pořadu explicitně označíme
    if "PodcastName" not in df.columns:
        df["PodcastName"] = pd.NA
    df["PodcastName"] = df["PodcastName"].astype("string")
    df["PodcastName"] = df["PodcastName"].fillna("Bez pořadu")
    df.loc[df["PodcastName"].str.strip() == "", "PodcastName"] = "Bez pořadu"

    return df


@st.cache_data
def load_monthly_yt(monthly_csv_path: str, monthly_csv_mtime: float) -> Optional[pd.DataFrame]:
    """Načte měsíční YouTube data (pokud existuje).

    `monthly_csv_mtime` se používá jen pro invalidaci cache při ruční editaci souboru.
    """
    _ = monthly_csv_mtime
    if not Path(monthly_csv_path).exists():
        return None
    df = pd.read_csv(monthly_csv_path)
    df["Měsíc"] = pd.to_datetime(df["Měsíc"] + "-01", errors="coerce")
    df["YouTube_Zhlédnutí"] = pd.to_numeric(df["YouTube_Zhlédnutí"], errors="coerce").fillna(0).astype(int)
    if "PodcastName" not in df.columns:
        df["PodcastName"] = ""
    df["PodcastName"] = df["PodcastName"].fillna("").astype("string")
    df.loc[df["PodcastName"].str.strip() == "", "PodcastName"] = "Bez pořadu"
    return df


@st.cache_data
def load_monthly_rc(monthly_csv_path: str, monthly_csv_mtime: float) -> Optional[pd.DataFrame]:
    """Načte měsíční Red Circle stažení po epizodách (pokud existuje export).

    `monthly_csv_mtime` se používá jen pro invalidaci cache při ruční editaci souboru.
    """
    _ = monthly_csv_mtime
    if not Path(monthly_csv_path).exists():
        return None
    df = pd.read_csv(monthly_csv_path)
    df["Měsíc"] = pd.to_datetime(df["Měsíc"].astype(str) + "-01", errors="coerce")
    df["RedCircle_Downloads"] = (
        pd.to_numeric(df["RedCircle_Downloads"], errors="coerce").fillna(0).astype(int)
    )
    if "Epizoda" not in df.columns:
        df["Epizoda"] = ""
    df["Epizoda"] = df["Epizoda"].fillna("").astype("string")
    if "PodcastName" not in df.columns:
        df["PodcastName"] = ""
    df["PodcastName"] = df["PodcastName"].fillna("").astype("string")
    df.loc[df["PodcastName"].str.strip() == "", "PodcastName"] = "Bez pořadu"
    return df


def render_overview(
    df: pd.DataFrame,
    df_all: pd.DataFrame,
    monthly_yt: Optional[pd.DataFrame],
    monthly_rc: Optional[pd.DataFrame],
):
    st.markdown("### Přehled výkonu online obsahu")
    total_downloads = df["Downloads"].sum()
    total_views = df["Zhlédnutí"].sum()
    total_usage = df["TotalUsage"].sum()
    usage_all_portfolio = float(df_all["TotalUsage"].sum())
    n_episodes = len(df)
    n_episodes_all = len(df_all)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Počet epizod",
        f"{fmt_tisice(n_episodes)}",
        help="Počet řádků v datech po zúžení levým filtrem (jedna řádka = jedna epizoda v přehledu).",
    )
    col2.metric(
        f"Celkem — {L_STAŽENÍ}",
        f"{fmt_tisice(total_downloads)}",
        help="Součet stažení epizod z Red Circle (podcasty; podle aktuálního výběru pořadů).",
    )
    col3.metric(
        f"Celkem — {L_ZHLÉDNUTÍ}",
        f"{fmt_tisice(total_views)}",
        help="Součet zhlédnutí videí na YouTube (podle aktuálního výběru pořadů).",
    )
    col4.metric(
        L_CELKEM_VYUŽITÍ,
        f"{fmt_tisice(total_usage)}",
        help=f"{L_STAŽENÍ} + {L_ZHLÉDNUTÍ}: jedna „jednotka využití“ = jedno stažení nebo jedno zhlédnutí.",
    )

    # ROI: náklady z data/naklady.csv + poměr běžícího roku podle posledního měsíce ve statistikách
    naklady = load_naklady_dict()
    period = resolve_stats_end_year_month()
    cost: Optional[float] = None
    if naklady and period:
        ey, em = period
        cost = total_cost_prorated(naklady, ey, em)

    st.markdown(f"### ROI podle ochoty platit (WTP {WTP_CZK} Kč)")
    if not naklady:
        st.caption(
            "Doplňte soubor **`data/naklady.csv`** (sloupce `rok`, `naklady_Kc`) s ročními náklady. "
            "ROI se nezobrazí, dokud soubor neexistuje."
        )
    elif not period:
        st.caption(
            "Chybí **měsíční export** (`data/MKP Studio - YouTube měsíčně.csv`) nebo **`data/statistiky_meta.json`**. "
            "Spusťte `combine_usage_data.py` s exportem **Data v grafu.csv** (měsíční data z YouTube)."
        )
    elif cost is not None and cost > 0 and n_episodes_all > 0 and n_episodes > 0 and total_usage > 0:
        # Náklady nejdou přiřadit ke konkrétní epizodě — alokujeme poměrně podle počtu epizod (řádků) ve výběru
        # oproti celému souboru. (Alokace podle podílu *využití* by matematicky dávala stejné % ROI pro každý
        # neprázdný výběr — podíl se vykrátí ve vzorci.)
        share_episodes = n_episodes / n_episodes_all
        cost_allocated = cost * share_episodes
        value_usage = total_usage * WTP_CZK
        roi = (value_usage - cost_allocated) / cost_allocated
        ey, em = period
        bd = cost_breakdown_lines(naklady, ey, em)
        pm = _proration_months_for_year(em)
        st.caption(
            f"Hodnota 1 využití = **{WTP_CZK} Kč** (ochota platit / WTP z [dotazníkového šetření VISK 2024]({WTP_SURVEY_URL})). "
            f"Vzorec: **(počet využití ve výběru × {WTP_CZK} Kč − alokované náklady) ÷ alokované náklady**. "
            f"**Celkové náklady** organizace = součet z **`data/naklady.csv`**: celé minulé roky + **({em}−1)/12 = {pm}/12** plánu za **{ey}** "
            f"(poslední měsíc v exportu **{em:02d}/{ey}** mínus jeden měsíc). "
            f"**Alokované náklady** = celkové náklady × **({n_episodes} epizod ve výběru / {n_episodes_all} v celém souboru) = {share_episodes:.1%}** → **{fmt_tisice(cost_allocated)} Kč** z **{fmt_tisice(cost)} Kč**. "
            "**0 %** = přínos = náklady; **kladné** = nad náklady; **záporné** = pod náklady."
        )
        with st.expander("Rozpis nákladů pro ROI", expanded=False):
            st.write(bd if bd else "(žádný řádek)")
            st.caption(
                f"**Celkové náklady (portfolio):** {fmt_tisice(cost)} Kč · "
                f"**Epizod ve výběru / v souboru:** {n_episodes} / {n_episodes_all} ({share_episodes:.1%}) · "
                f"**{L_CELKEM_VYUŽITÍ} (výběr / celý soubor):** {fmt_tisice(total_usage)} / {fmt_tisice(usage_all_portfolio)} · "
                f"**alokované náklady:** {fmt_tisice(cost_allocated)} Kč"
            )
        st.metric(
            f"ROI (WTP {WTP_CZK} Kč/využití)",
            f"{roi:.0%}",
            help=(
                f"Předpoklad: 1 jednotka ({L_STAŽENÍ} nebo {L_ZHLÉDNUTÍ}) = {WTP_CZK} Kč v přínosu, "
                f"dle ochoty platit (WTP) z dotazníkového šetření VISK 2024. "
                f"[Výsledky šetření (PDF)]({WTP_SURVEY_URL})"
            ),
        )
        roi_long = pd.DataFrame(
            {
                "Kategorie": ["Hodnota využití", "Alokované náklady"],
                "Kč": [value_usage, cost_allocated],
            }
        )
        roi_chart = (
            alt.Chart(roi_long)
            .mark_bar()
            .encode(
                x=alt.X("Kategorie:N", title=None, sort=["Hodnota využití", "Alokované náklady"]),
                y=alt.Y("Kč:Q", title="Kč"),
                color=alt.Color("Kategorie:N", title=None, legend=None),
                tooltip=[
                    alt.Tooltip("Kategorie:N"),
                    alt.Tooltip("Kč:Q", format=","),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(alt_cz(roi_chart), use_container_width=True)

        roi_series = build_cumulative_roi_series(
            df, df_all, monthly_yt, monthly_rc, naklady, ey, em
        )
        if len(roi_series) > 0:
            roi_series_plot = roi_series.copy()
            roi_series_plot["ROI_pct"] = roi_series_plot["ROI"] * 100.0
            first_cost_month = roi_series_plot.loc[
                roi_series_plot["Náklady alok"] > 0, "Měsíc"
            ].min()
            reference_months = roi_series_plot.loc[
                roi_series_plot["Měsíc"] >= first_cost_month, "Měsíc"
            ].reset_index(drop=True)
            reference = pd.DataFrame(
                {
                    "Měsíc": reference_months,
                    "ROI_pct": [0.0] * len(reference_months),
                    "Řada": ["Cíl 0 % (návratnost nákladů)"] * len(reference_months),
                }
            )
            actual = roi_series_plot[["Měsíc", "ROI_pct"]].copy()
            actual["Řada"] = "Kumulativní ROI"
            roi_line_data = with_mesic_popis(
                pd.concat([actual, reference], ignore_index=True)
            )
            roi_line_chart = (
                alt.Chart(roi_line_data)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Měsíc:T", title="Měsíc / rok", axis=alt.Axis(format="%m/%Y")),
                    y=alt.Y("ROI_pct:Q", title="ROI (%)"),
                    color=alt.Color("Řada:N", title=None),
                    strokeDash=alt.StrokeDash(
                        "Řada:N",
                        title=None,
                        sort=["Kumulativní ROI", "Cíl 0 % (návratnost nákladů)"],
                    ),
                    tooltip=[
                        alt.Tooltip("Měsíc_popis:N", title="Měsíc"),
                        alt.Tooltip("Řada:N", title="Řada"),
                        alt.Tooltip("ROI_pct:Q", title="ROI (%)", format=".1f"),
                    ],
                )
                .properties(height=320)
            )
            st.markdown("#### Kumulativní ROI v čase")
            episodes_in_scope = set(df["EpisodeName"])
            has_rc_monthly = (
                monthly_rc is not None
                and len(monthly_rc) > 0
                and monthly_rc["Epizoda"].isin(episodes_in_scope).any()
            )
            if has_rc_monthly:
                st.caption(
                    "Kumulativní ROI aktuálního výběru. Osa zobrazuje měsíc i rok. "
                    "YouTube i Red Circle berou skutečná měsíční data. "
                    "Náklady se alokují stejným podílem epizod jako výše; "
                    "před prvním měsícem s náklady se ROI ještě nekreslí."
                )
            else:
                st.caption(
                    "Kumulativní ROI aktuálního výběru. Osa zobrazuje měsíc i rok. "
                    "YouTube podle měsíčních dat; u Red Circle chybí měsíční export, "
                    "proto se stažení dočasně přiřadí k měsíci publikace epizody. "
                    "Náklady se alokují stejným podílem epizod jako výše; "
                    "před prvním měsícem s náklady se ROI ještě nekreslí."
                )
            st.altair_chart(alt_cz(roi_line_chart), use_container_width=True)
    elif cost is not None and cost > 0 and n_episodes_all <= 0:
        st.caption("V datech nejsou žádné epizody – ROI nelze spočítat.")
    elif cost is not None and cost > 0 and total_usage <= 0:
        st.caption(
            f"Ve vybraném filtru není žádné **{L_CELKEM_VYUŽITÍ.lower()}** – ROI pro výběr nelze spočítat (alokované náklady by byly 0 Kč)."
        )
    elif cost is not None and cost <= 0:
        st.caption("Součet nákladů je v tomto nastavení 0 – ROI nelze spočítat.")
    else:
        st.caption("Pro vypočtení ROI doplňte náklady a měsíční statistiky (viz výše).")


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtry")
    podcasts = sorted(df["PodcastName"].unique())
    if "podcasts_sel" not in st.session_state:
        st.session_state["podcasts_sel"] = podcasts
    else:
        # Sanitizace: pokud se změnil seznam pořadů (např. po ruční editaci CSV),
        # ponecháme jen ty, které skutečně existují v aktuálním datasetu.
        st.session_state["podcasts_sel"] = [
            p for p in st.session_state["podcasts_sel"] if p in podcasts
        ]

    c_all, c_none = st.sidebar.columns(2)
    if c_all.button("Všechny"):
        st.session_state["podcasts_sel"] = podcasts
    if c_none.button("Žádné"):
        st.session_state["podcasts_sel"] = []

    sel_podcasts = st.sidebar.multiselect(
        f"{L_POŘAD} (filtr)",
        podcasts,
        st.session_state["podcasts_sel"],
        key="podcasts_sel",
    )

    q_show = st.sidebar.text_input("Vyhledat v názvu pořadu", "").strip()
    q_episode = st.sidebar.text_input("Vyhledat v názvu epizody/dílu", "").strip()

    # Filtr podle období publikace jsme na základě požadavku odstranili –
    # ve výchozím stavu zobrazujeme všechny epizody bez časového omezení.
    mask_date = pd.Series(True, index=df.index)

    mask = df["PodcastName"].isin(sel_podcasts) & mask_date
    if q_show:
        mask &= df["PodcastName"].astype("string").str.contains(q_show, case=False, na=False)
    if q_episode:
        mask &= df["EpisodeName"].astype("string").str.contains(q_episode, case=False, na=False)
    return df[mask]


def chart_top_episodes(df: pd.DataFrame):
    st.markdown(f"### Top epizody podle {L_CELKEM_VYUŽITÍ_GEN}")
    top_n = st.slider("Počet epizod v přehledu", 5, 30, 10)
    top = df.sort_values("TotalUsage", ascending=False).head(top_n)

    chart = (
        alt.Chart(top)
        .mark_bar()
        .encode(
            x=alt.X("TotalUsage:Q", title=L_CELKEM_VYUŽITÍ),
            y=alt.Y("EpisodeName:N", sort="-x", title=L_EPIZODA),
            color=alt.Color("PodcastName:N", title=L_POŘAD),
            tooltip=[
                alt.Tooltip("EpisodeName:N", title=L_EPIZODA),
                alt.Tooltip("PodcastName:N", title=L_POŘAD),
                alt.Tooltip("Downloads:Q", title=L_STAŽENÍ, format=","),
                alt.Tooltip("Zhlédnutí:Q", title=L_ZHLÉDNUTÍ, format=","),
                alt.Tooltip("TotalUsage:Q", title=L_CELKEM_VYUŽITÍ, format=","),
            ],
        )
        .properties(height=400)
    )
    st.altair_chart(alt_cz(chart), use_container_width=True)


def chart_downloads_vs_views(df: pd.DataFrame):
    st.markdown(f"### Vztah: {L_STAŽENÍ} a {L_ZHLÉDNUTÍ}")
    chart = (
        alt.Chart(df)
        .mark_circle(opacity=0.6)
        .encode(
            x=alt.X("Downloads:Q", title=L_STAŽENÍ),
            y=alt.Y("Zhlédnutí:Q", title=L_ZHLÉDNUTÍ),
            color=alt.Color("PodcastName:N", title=L_POŘAD),
            size=alt.Size(
                "TotalUsage:Q",
                title=L_CELKEM_VYUŽITÍ,
                scale=alt.Scale(range=[30, 400]),
            ),
            tooltip=[
                alt.Tooltip("EpisodeName:N", title=L_EPIZODA),
                alt.Tooltip("PodcastName:N", title=L_POŘAD),
                alt.Tooltip("Downloads:Q", title=L_STAŽENÍ, format=","),
                alt.Tooltip("Zhlédnutí:Q", title=L_ZHLÉDNUTÍ, format=","),
                alt.Tooltip("TotalUsage:Q", title=L_CELKEM_VYUŽITÍ, format=","),
            ],
        )
        .properties(height=400)
    )
    st.altair_chart(alt_cz(chart), use_container_width=True)


def chart_time_trend(
    df: pd.DataFrame,
    monthly_yt: Optional[pd.DataFrame],
    monthly_rc: Optional[pd.DataFrame],
):
    st.markdown("### Trend využití v čase")
    has_yt = monthly_yt is not None and len(monthly_yt) > 0
    has_rc = monthly_rc is not None and len(monthly_rc) > 0
    if has_yt and has_rc:
        st.caption(
            f"Měsíční součty {L_ZHLÉDNUTÍ.lower()} (YouTube) a {L_STAŽENÍ.lower()} (Red Circle) "
            "pro epizody ve zvoleném filtru."
        )
    elif has_yt:
        st.caption(
            f"Měsíční součty {L_ZHLÉDNUTÍ.lower()} na YouTube. "
            "U Red Circle chybí měsíční export – trend stažení se nezobrazí."
        )
    elif has_rc:
        st.caption(
            f"Měsíční součty {L_STAŽENÍ.lower()} na Red Circle. "
            "Pro YouTube trend spusťte `combine_usage_data.py` s exportem Data v grafu.csv."
        )
    else:
        st.info(
            "Pro trend v čase chybí měsíční data. "
            "YouTube: spusťte `combine_usage_data.py` s Data v grafu.csv. "
            "Red Circle: přidejte `data/MKP Studio - Red Circle měsíčně.csv`."
        )
        return

    episodes_in_scope = set(df["EpisodeName"])
    frames: list[pd.DataFrame] = []

    if has_yt:
        m_yt = monthly_yt[monthly_yt["Epizoda"].isin(episodes_in_scope)]
        if len(m_yt) > 0:
            g_yt = m_yt.groupby("Měsíc", as_index=False)["YouTube_Zhlédnutí"].sum()
            g_yt = g_yt.rename(columns={"YouTube_Zhlédnutí": "Hodnota"})
            g_yt["Zdroj"] = L_ZHLÉDNUTÍ_YT_POPIS
            frames.append(g_yt)

    if has_rc:
        m_rc = monthly_rc[monthly_rc["Epizoda"].isin(episodes_in_scope)]
        if len(m_rc) > 0:
            g_rc = m_rc.groupby("Měsíc", as_index=False)["RedCircle_Downloads"].sum()
            g_rc = g_rc.rename(columns={"RedCircle_Downloads": "Hodnota"})
            g_rc["Zdroj"] = L_STAŽENÍ_RC_POPIS
            frames.append(g_rc)

    if not frames:
        st.info("Pro zvolený filtr pořadu nejsou v měsíčních datech žádné hodnoty.")
        return

    combined = pd.concat(frames, ignore_index=True)
    nonzero = combined[combined["Hodnota"] > 0].copy()

    st.checkbox(
        "Zobrazit i měsíce s 0 využitím",
        value=False,
        key="show_zero_trend",
    )
    show_zeros = bool(st.session_state.get("show_zero_trend", False))
    to_plot = with_mesic_popis(combined if show_zeros else nonzero)

    if len(to_plot) > 0:
        chart = (
            alt.Chart(to_plot)
            .mark_line(point=True)
            .encode(
                x=alt.X("Měsíc:T", title="Měsíc", axis=alt.Axis(format="%m/%Y")),
                y=alt.Y("Hodnota:Q", title="Využití"),
                color=alt.Color("Zdroj:N", title=None),
                tooltip=[
                    alt.Tooltip("Měsíc_popis:N", title="Měsíc"),
                    alt.Tooltip("Zdroj:N", title="Zdroj"),
                    alt.Tooltip("Hodnota:Q", title="Využití", format=","),
                ],
            )
            .properties(height=350)
        )
        st.altair_chart(alt_cz(chart), use_container_width=True)
        n_months = to_plot["Měsíc"].nunique()
        n_nonzero = nonzero["Měsíc"].nunique()
        n_all = combined["Měsíc"].nunique()
        st.caption(
            f"Zobrazeno {n_months} měsíců "
            f"(nenulové: {n_nonzero} / celkem: {n_all})."
        )
    else:
        st.info("Pro zvolený filtr pořadu nejsou v měsíčních datech žádné nenulové hodnoty.")


def chart_source_mix(df: pd.DataFrame):
    total_downloads = df["Downloads"].sum()
    total_views = df["Zhlédnutí"].sum()
    total_usage = total_downloads + total_views
    share_downloads = total_downloads / total_usage if total_usage else 0
    share_views = total_views / total_usage if total_usage else 0

    st.markdown(f"### Rozdělení {L_CELKEM_VYUŽITÍ_GEN} podle zdroje")

    pie_data = pd.DataFrame(
        {
            "Platforma": [L_STAŽENÍ_RC_POPIS, L_ZHLÉDNUTÍ_YT_POPIS],
            "Hodnota": [total_downloads, total_views],
            "Podíl": [share_downloads, share_views],
        }
    )

    pie_chart = (
        alt.Chart(pie_data)
        .mark_arc(innerRadius=0)
        .encode(
            theta=alt.Theta("Hodnota:Q", stack=True),
            color=alt.Color(
                "Platforma:N",
                scale=alt.Scale(
                    domain=[L_STAŽENÍ_RC_POPIS, L_ZHLÉDNUTÍ_YT_POPIS],
                    range=["#1f77b4", "#ff7f0e"],
                ),
                title="Zdroj",
            ),
            tooltip=[
                "Platforma",
                alt.Tooltip("Hodnota:Q", title="Hodnota", format=","),
                alt.Tooltip("Podíl:Q", title="Podíl", format=".0%"),
            ],
        )
        .properties(height=400, title=f"Podíl {L_CELKEM_VYUŽITÍ_GEN} podle zdroje")
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        st.altair_chart(alt_cz(pie_chart), use_container_width=True)
    with col2:
        st.markdown(
            f"- **Podíl — {L_STAŽENÍ_RC_POPIS}**: {share_downloads:.0%}.\n"
            f"- **Podíl — {L_ZHLÉDNUTÍ_YT_POPIS}**: {share_views:.0%}.\n\n"
            f"- **Celkem — {L_STAŽENÍ_RC_POPIS}**: {fmt_tisice(total_downloads)}\n"
            f"- **Celkem — {L_ZHLÉDNUTÍ_YT_POPIS}**: {fmt_tisice(total_views)}\n"
            f"- **{L_CELKEM_VYUŽITÍ}**: {fmt_tisice(total_usage)}"
        )


def chart_pareto_top_episodes(df: pd.DataFrame):
    st.markdown("### Koncentrace využití")
    top_n = st.slider("Počet top epizod pro odhad koncentrace", 5, 50, 25, key="pareto_top_n")

    sorted_df = df.sort_values("TotalUsage", ascending=False)
    total_usage = float(sorted_df["TotalUsage"].sum())
    n_all = len(sorted_df)
    if n_all == 0 or total_usage <= 0:
        st.info("Pro zvolený filtr nelze spočítat koncentraci využití.")
        return

    top = sorted_df.head(top_n).copy().reset_index(drop=True)
    top["Pořadí"] = top.index + 1
    top["Podíl kumulativně"] = top["TotalUsage"].cumsum() / total_usage
    share = float(top["Podíl kumulativně"].iloc[-1])
    n_top = len(top)
    share_eps = n_top / n_all

    if share >= 0.8:
        verdict = "portfolio je silně závislé na menším počtu titulů"
    elif share >= 0.5:
        verdict = "využití je spíš koncentrované v horní části žebříčku"
    else:
        verdict = "využití je relativně rovnoměrně rozložené"

    st.markdown(
        f"Top **{n_top}** epizod ({share_eps:.0%} katalogu) pokrývá **{share:.0%}** "
        f"{L_CELKEM_VYUŽITÍ_GEN} — {verdict}."
    )
    st.caption(
        "Konkrétní tituly hledejte v žebříčku Top epizody a v analytických vhledech. "
        "Vodorovná čára = 80 % využití."
    )

    curve = alt.Chart(top).mark_line(point=True).encode(
        x=alt.X("Pořadí:Q", title="Pořadí"),
        y=alt.Y(
            "Podíl kumulativně:Q",
            title=None,
            axis=alt.Axis(format="%"),
            scale=alt.Scale(domain=[0, 1]),
        ),
        tooltip=[
            alt.Tooltip("EpisodeName:N", title=L_EPIZODA),
            alt.Tooltip("TotalUsage:Q", title=L_CELKEM_VYUŽITÍ, format=","),
            alt.Tooltip("Podíl kumulativně:Q", title="Kumulativně", format=".0%"),
        ],
    )
    ref80 = (
        alt.Chart(pd.DataFrame({"y": [0.8]}))
        .mark_rule(strokeDash=[4, 4], color="#888")
        .encode(y="y:Q")
    )
    chart = (curve + ref80).properties(height=150)
    st.altair_chart(alt_cz(chart), use_container_width=True)


def render_monthly_top_episodes(
    df: pd.DataFrame,
    monthly_yt: Optional[pd.DataFrame],
    monthly_rc: Optional[pd.DataFrame],
):
    st.markdown(f"### Měsíční top epizoda ({L_CELKEM_VYUŽITÍ})")
    has_yt = monthly_yt is not None and len(monthly_yt) > 0
    has_rc = monthly_rc is not None and len(monthly_rc) > 0
    if not has_yt and not has_rc:
        st.info(
            "Měsíční data nejsou dostupná (YouTube ani Red Circle). "
            "Doplňte měsíční CSV a obnovte stránku."
        )
        return

    if has_yt and has_rc:
        st.caption(
            f"Žebříček podle součtu {L_ZHLÉDNUTÍ.lower()} (YouTube) a {L_STAŽENÍ.lower()} (Red Circle) "
            "ve zvoleném měsíci."
        )
    elif has_yt:
        st.caption(
            f"Zatím jen {L_ZHLÉDNUTÍ.lower()} (YouTube) — chybí `MKP Studio - Red Circle měsíčně.csv`."
        )
    else:
        st.caption(
            f"Zatím jen {L_STAŽENÍ.lower()} (Red Circle) — chybí YouTube měsíční export."
        )

    episodes_in_scope = set(df["EpisodeName"])
    ep_to_podcast = (
        df[["EpisodeName", "PodcastName"]]
        .drop_duplicates("EpisodeName")
        .set_index("EpisodeName")["PodcastName"]
        .to_dict()
    )

    frames: list[pd.DataFrame] = []
    if has_yt:
        m_yt = monthly_yt[monthly_yt["Epizoda"].isin(episodes_in_scope)].copy()
        if len(m_yt) > 0:
            g = m_yt.groupby(["Měsíc", "Epizoda"], as_index=False)["YouTube_Zhlédnutí"].sum()
            g = g.rename(columns={"YouTube_Zhlédnutí": "Zhlédnutí"})
            frames.append(g[["Měsíc", "Epizoda", "Zhlédnutí"]])
    if has_rc:
        m_rc = monthly_rc[monthly_rc["Epizoda"].isin(episodes_in_scope)].copy()
        if len(m_rc) > 0:
            g = m_rc.groupby(["Měsíc", "Epizoda"], as_index=False)["RedCircle_Downloads"].sum()
            g = g.rename(columns={"RedCircle_Downloads": "Downloads"})
            frames.append(g[["Měsíc", "Epizoda", "Downloads"]])

    if not frames:
        st.info("Pro zvolený filtr pořadu nejsou v měsíčních datech žádné hodnoty.")
        return

    merged = frames[0]
    for extra in frames[1:]:
        merged = merged.merge(extra, on=["Měsíc", "Epizoda"], how="outer")
    if "Zhlédnutí" not in merged.columns:
        merged["Zhlédnutí"] = 0
    if "Downloads" not in merged.columns:
        merged["Downloads"] = 0
    merged["Zhlédnutí"] = merged["Zhlédnutí"].fillna(0).astype(int)
    merged["Downloads"] = merged["Downloads"].fillna(0).astype(int)
    merged["TotalUsage"] = merged["Zhlédnutí"] + merged["Downloads"]
    merged["PodcastName"] = merged["Epizoda"].map(ep_to_podcast).fillna("Bez pořadu")

    monthly_totals = merged.groupby("Měsíc", as_index=False)["TotalUsage"].sum()
    monthly_totals = monthly_totals[monthly_totals["TotalUsage"] > 0].copy()
    if len(monthly_totals) == 0:
        st.info("Neexistují měsíce s nenulovým využitím zvoleného výběru.")
        return

    monthly_totals["Měsíc_str"] = monthly_totals["Měsíc"].dt.strftime("%Y-%m")
    month_options = sorted(monthly_totals["Měsíc_str"].unique().tolist())
    selected_month_str = st.selectbox(
        "Vyber měsíc",
        month_options,
        format_func=lambda s: format_mesic_cz(f"{s}-01"),
    )

    top_n = st.slider("Počet top epizod v měsíci", 3, 10, 5)

    month_dt = monthly_totals.loc[
        monthly_totals["Měsíc_str"] == selected_month_str, "Měsíc"
    ].iloc[0]

    top_month = (
        merged[merged["Měsíc"] == month_dt]
        .groupby(["Epizoda", "PodcastName"], as_index=False)[["Downloads", "Zhlédnutí", "TotalUsage"]]
        .sum()
        .sort_values("TotalUsage", ascending=False)
        .head(top_n)
    )

    out = top_month.rename(columns={"Epizoda": "EpisodeName"})
    out = out[["EpisodeName", "PodcastName", "Downloads", "Zhlédnutí", "TotalUsage"]]
    st.dataframe(dataframe_display_labels(out), use_container_width=True)


def render_insights(df: pd.DataFrame):
    st.markdown("### Analytické vhledy")

    top_n = st.slider("Počet epizod v tabulce vhledů", 5, 20, 10)
    top = df.sort_values("TotalUsage", ascending=False).head(top_n)
    st.markdown(f"**Nejsilnější epizody** (TOP {top_n} podle {L_CELKEM_VYUŽITÍ_GEN}):")
    st.dataframe(
        dataframe_display_labels(
            top[["EpisodeName", "PodcastName", "Downloads", "Zhlédnutí", "TotalUsage"]]
        ),
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown(f"**Celkové využití podle {L_POŘADU}:**")

    by_podcast_total = (
        df.groupby("PodcastName", dropna=False)[["Downloads", "Zhlédnutí", "TotalUsage"]]
        .sum()
        .sort_values("TotalUsage", ascending=False)
        .reset_index()
    )
    top_podcast = 10
    chart_df = by_podcast_total.head(top_podcast)
    if len(chart_df) > 0 and chart_df["TotalUsage"].sum() > 0:
        podcast_order = chart_df["PodcastName"].tolist()
        long = chart_df.melt(
            id_vars=["PodcastName"],
            value_vars=["Downloads", "Zhlédnutí"],
            var_name="_metric",
            value_name="Hodnota",
        )
        long["Zdroj"] = long["_metric"].map(
            {
                "Downloads": L_STAŽENÍ_RC_POPIS,
                "Zhlédnutí": L_ZHLÉDNUTÍ_YT_POPIS,
            }
        )
        height = max(220, 28 * len(podcast_order) + 80)
        podcast_chart = (
            alt.Chart(long)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "PodcastName:N",
                    sort=podcast_order,
                    title=L_POŘAD,
                ),
                x=alt.X("Hodnota:Q", title=L_CELKEM_VYUŽITÍ, stack="zero"),
                color=alt.Color(
                    "Zdroj:N",
                    title=None,
                    scale=alt.Scale(
                        domain=[L_STAŽENÍ_RC_POPIS, L_ZHLÉDNUTÍ_YT_POPIS],
                        range=["#1f77b4", "#ff7f0e"],
                    ),
                    sort=[L_STAŽENÍ_RC_POPIS, L_ZHLÉDNUTÍ_YT_POPIS],
                ),
                tooltip=[
                    alt.Tooltip("PodcastName:N", title=L_POŘAD),
                    alt.Tooltip("Zdroj:N", title="Zdroj"),
                    alt.Tooltip("Hodnota:Q", title="Využití", format=","),
                ],
            )
            .properties(height=height)
        )
        st.altair_chart(alt_cz(podcast_chart), use_container_width=True)
        st.caption(
            f"TOP {min(top_podcast, len(chart_df))} pořadů podle {L_CELKEM_VYUŽITÍ_GEN.lower()}; "
            f"sloupce = {L_STAŽENÍ.lower()} (Red Circle) + {L_ZHLÉDNUTÍ.lower()} (YouTube)."
        )
    st.dataframe(
        dataframe_display_labels(by_podcast_total.head(top_podcast)),
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown(f"**Top pořady podle {L_STAŽENÍ_RC_POPIS}:**")
    by_podcast_downloads = (
        df.groupby("PodcastName", dropna=False)["Downloads"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    st.dataframe(dataframe_display_labels(by_podcast_downloads.head(top_podcast)), use_container_width=True)

    st.markdown("---")
    st.markdown(f"**Top pořady podle {L_ZHLÉDNUTÍ_YT_POPIS}:**")
    by_podcast_views = (
        df.groupby("PodcastName", dropna=False)["Zhlédnutí"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    st.dataframe(dataframe_display_labels(by_podcast_views.head(top_podcast)), use_container_width=True)


def main():
    st.set_page_config(page_title="Analýza online obsahu (Red Circle + YouTube)", layout="wide")
    st.title("Analýza využití online obsahu (Red Circle + YouTube)")
    st.caption(
        "Data: `data/MKP Studio - statistika.csv` — sloučená data (Red Circle: podcasty, YouTube: videa)."
    )

    try:
        csv_mtime = CSV_PATH.stat().st_mtime if CSV_PATH.exists() else 0.0
        df = load_data(str(CSV_PATH), csv_mtime)
    except FileNotFoundError:
        st.error(
            f"Soubor s daty nebyl nalezen. "
            f"Zkontrolujte, prosím, že existuje `data/MKP Studio - statistika.csv` "
            f"v adresáři: {BASE_DIR}"
        )
        return

    filtered = render_filters(df)
    if filtered.empty:
        st.warning("Pro zvolené filtry nejsou žádná data.")
        return

    monthly_mtime = MONTHLY_CSV_PATH.stat().st_mtime if MONTHLY_CSV_PATH.exists() else 0.0
    monthly_yt = load_monthly_yt(str(MONTHLY_CSV_PATH), monthly_mtime)
    monthly_rc_mtime = (
        MONTHLY_RC_CSV_PATH.stat().st_mtime if MONTHLY_RC_CSV_PATH.exists() else 0.0
    )
    monthly_rc = load_monthly_rc(str(MONTHLY_RC_CSV_PATH), monthly_rc_mtime)
    render_overview(filtered, df, monthly_yt, monthly_rc)
    chart_time_trend(filtered, monthly_yt, monthly_rc)

    chart_source_mix(filtered)

    col1, col2 = st.columns(2)
    with col1:
        chart_top_episodes(filtered)
    with col2:
        chart_downloads_vs_views(filtered)

    chart_pareto_top_episodes(filtered)
    render_monthly_top_episodes(filtered, monthly_yt, monthly_rc)

    render_insights(filtered)


if __name__ == "__main__":
    import sys
    import subprocess
    import os
    
    # Jednoduchá detekce: pokud není nastavena proměnná prostředí, kterou Streamlit nastavuje,
    # nebo pokud skript není spuštěn přes streamlit run, spustíme ho automaticky
    # Zkontrolujeme, jestli je Streamlit runtime aktivní pokusem o přístup k runtime kontextu
    try:
        # Pokud Streamlit runtime běží, můžeme přistupovat k session_state
        _ = st.session_state
        # Pokud jsme tady, Streamlit runtime běží
        main()
    except (AttributeError, RuntimeError):
        # Streamlit runtime není aktivní, spustíme ho automaticky
        print("Spouštím Streamlit aplikaci...")
        print("(Pokud vidíte tuto zprávu opakovaně, použijte: python3 -m streamlit run streamlit_media_analytics.py)")
        result = subprocess.run([sys.executable, "-m", "streamlit", "run", __file__] + sys.argv[1:])
        sys.exit(result.returncode)


