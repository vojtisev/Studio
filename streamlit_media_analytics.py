import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from typing import Optional


# CSV ve složce data/ vedle skriptu
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "MKP Studio - statistika.csv"
MONTHLY_CSV_PATH = DATA_DIR / "MKP Studio - YouTube měsíčně.csv"


@st.cache_data
def load_data() -> pd.DataFrame:
    """Načte data z CSV a převede názvy sloupců na standardní formát."""
    df = pd.read_csv(CSV_PATH)

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
    df["Downloads"] = pd.to_numeric(df["Downloads"], errors="coerce").fillna(0).astype(int)
    df["Zhlédnutí"] = pd.to_numeric(df["Zhlédnutí"], errors="coerce").fillna(0).astype(int)
    if "TotalUsage" not in df.columns:
        df["TotalUsage"] = df["Downloads"] + df["Zhlédnutí"]

    # normalizace názvů pořadů – epizody bez pořadu explicitně označíme
    if "PodcastName" not in df.columns:
        df["PodcastName"] = pd.NA
    df["PodcastName"] = df["PodcastName"].astype("string")
    df["PodcastName"] = df["PodcastName"].fillna("Bez pořadu")
    df.loc[df["PodcastName"].str.strip() == "", "PodcastName"] = "Bez pořadu"

    return df


@st.cache_data
def load_monthly_yt() -> Optional[pd.DataFrame]:
    """Načte měsíční YouTube data (pokud existuje). RedCircle měsíční rozpad nemá."""
    if not MONTHLY_CSV_PATH.exists():
        return None
    df = pd.read_csv(MONTHLY_CSV_PATH)
    df["Měsíc"] = pd.to_datetime(df["Měsíc"] + "-01", errors="coerce")
    df["YouTube_Zhlédnutí"] = pd.to_numeric(df["YouTube_Zhlédnutí"], errors="coerce").fillna(0).astype(int)
    if "PodcastName" not in df.columns:
        df["PodcastName"] = ""
    df["PodcastName"] = df["PodcastName"].fillna("").astype("string")
    df.loc[df["PodcastName"].str.strip() == "", "PodcastName"] = "Bez pořadu"
    return df


def render_overview(df: pd.DataFrame):
    st.markdown("### Přehled výkonu online obsahu")
    total_downloads = df["Downloads"].sum()
    total_views = df["Zhlédnutí"].sum()
    total_usage = df["TotalUsage"].sum()
    n_episodes = len(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Počet epizod", f"{n_episodes:,}")
    col2.metric("Celkem stažení (RedCircle)", f"{total_downloads:,}")
    col3.metric("Celkem zhlédnutí (YouTube)", f"{total_views:,}")
    col4.metric("Celkové využití", f"{total_usage:,}")

    # Základní ROI ukazatele (roční náklady 800 000 Kč)
    cost = 800_000
    if cost > 0 and total_usage > 0:
        roi_pess = (total_usage * 3 - cost) / cost
        roi_real = (total_usage * 10 - cost) / cost
        roi_opt = (total_usage * 30 - cost) / cost

        st.markdown("### Odhad ROI podle hodnoty jednoho využití")
        r1, r2, r3 = st.columns(3)
        r1.metric("ROI – pesimistický (3 Kč/využití)", f"{roi_pess:.0%}")
        r2.metric("ROI – realistický (10 Kč/využití)", f"{roi_real:.0%}")
        r3.metric("ROI – optimistický (30 Kč/využití)", f"{roi_opt:.0%}")


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtry")
    podcasts = sorted(df["PodcastName"].unique())
    sel_podcasts = st.sidebar.multiselect("Podcast / pořad", podcasts, podcasts)

    # Filtr podle období publikace jsme na základě požadavku odstranili –
    # ve výchozím stavu zobrazujeme všechny epizody bez časového omezení.
    mask_date = pd.Series(True, index=df.index)

    filtered = df[df["PodcastName"].isin(sel_podcasts) & mask_date]
    return filtered


def chart_top_episodes(df: pd.DataFrame):
    st.markdown("### Top epizody podle celkového využití")
    top_n = st.slider("Počet epizod v přehledu", 5, 30, 10)
    top = df.sort_values("TotalUsage", ascending=False).head(top_n)

    chart = (
        alt.Chart(top)
        .mark_bar()
        .encode(
            x=alt.X("TotalUsage:Q", title="Celkové využití (stažení + zhlédnutí)"),
            y=alt.Y("EpisodeName:N", sort="-x", title="Epizoda"),
            color=alt.Color("PodcastName:N", title="Podcast / pořad"),
            tooltip=[
                "EpisodeName",
                "PodcastName",
                alt.Tooltip("Downloads:Q", title="Stažení"),
                alt.Tooltip("Zhlédnutí:Q", title="Zhlédnutí"),
                alt.Tooltip("TotalUsage:Q", title="Celkové využití"),
            ],
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)


def chart_downloads_vs_views(df: pd.DataFrame):
    st.markdown("### Vztah mezi staženími a zhlédnutími")
    chart = (
        alt.Chart(df)
        .mark_circle(size=80, opacity=0.6)
        .encode(
            x=alt.X("Downloads:Q", title="Stažení (RedCircle)"),
            y=alt.Y("Zhlédnutí:Q", title="Zhlédnutí (YouTube)"),
            color=alt.Color("PodcastName:N", title="Podcast / pořad"),
            tooltip=["EpisodeName", "PodcastName", "Downloads", "Zhlédnutí", "TotalUsage"],
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)


def chart_time_trend(df: pd.DataFrame, monthly_yt: Optional[pd.DataFrame]):
    st.markdown("### Trend využití v čase (YouTube)")
    st.caption("Časový trend zobrazujeme jen z YouTube – měsíční data máme k dispozici pouze tam. RedCircle nabízí jen celkové stažení a datum publikace.")

    if monthly_yt is not None and len(monthly_yt) > 0:
        episodes_in_scope = set(df["EpisodeName"])
        m = monthly_yt[monthly_yt["Epizoda"].isin(episodes_in_scope)]
        if len(m) > 0:
            grouped_yt = m.groupby("Měsíc", as_index=False)["YouTube_Zhlédnutí"].sum()
            chart_yt = (
                alt.Chart(grouped_yt)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Měsíc:T", title="Měsíc"),
                    y=alt.Y("YouTube_Zhlédnutí:Q", title="Zhlédnutí (YouTube)"),
                    tooltip=[
                        alt.Tooltip("Měsíc:T", title="Měsíc"),
                        alt.Tooltip("YouTube_Zhlédnutí:Q", title="Zhlédnutí"),
                    ],
                )
                .properties(height=350)
            )
            st.altair_chart(chart_yt, use_container_width=True)
        else:
            st.info("Pro zvolený filtr pořadu nejsou v měsíčních datech žádná YouTube zhlédnutí.")
    else:
        st.info("Pro zobrazení trendu spusťte nejdříve skript `combine_usage_data.py` s exportem měsíčních YouTube dat (soubor Data v grafu.csv ve formátu po měsících).")


def render_insights(df: pd.DataFrame):
    st.markdown("### Analytické vhledy")

    # 1) které epizody táhnou nejvíc
    top = df.sort_values("TotalUsage", ascending=False).head(5)
    st.markdown("**Nejsilnější epizody** (TOP 5 podle celkového využití):")
    st.dataframe(
        top[["EpisodeName", "PodcastName", "Downloads", "Zhlédnutí", "TotalUsage"]],
        use_container_width=True,
    )

    # 2) podíl stažení vs. zhlédnutí
    total_downloads = df["Downloads"].sum()
    total_views = df["Zhlédnutí"].sum()
    total_usage = total_downloads + total_views
    share_downloads = total_downloads / total_usage if total_usage else 0
    share_views = total_views / total_usage if total_usage else 0

    st.markdown("**Rozdělení využití podle platformy:**")
    
    # Příprava dat pro koláčový graf
    pie_data = pd.DataFrame({
        "Platforma": ["Stažení (podcasty)", "Zhlédnutí (YouTube)"],
        "Hodnota": [total_downloads, total_views],
        "Podíl": [share_downloads, share_views]
    })
    
    # Koláčový graf pomocí Altair
    pie_chart = (
        alt.Chart(pie_data)
        .mark_arc(innerRadius=0)
        .encode(
            theta=alt.Theta("Hodnota:Q", stack=True),
            color=alt.Color(
                "Platforma:N",
                scale=alt.Scale(
                    domain=["Stažení (podcasty)", "Zhlédnutí (YouTube)"],
                    range=["#1f77b4", "#ff7f0e"]
                ),
                title="Platforma"
            ),
            tooltip=[
                "Platforma",
                alt.Tooltip("Hodnota:Q", title="Hodnota", format=","),
                alt.Tooltip("Podíl:Q", title="Podíl", format=".0%")
            ]
        )
        .properties(height=400, title="Podíl využití podle platformy")
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.altair_chart(pie_chart, use_container_width=True)
    with col2:
        st.markdown(
            f"- **Podíl stažení (podcasty)**: {share_downloads:.0%} z celkového využití.\n"
            f"- **Podíl zhlédnutí (YouTube)**: {share_views:.0%} z celkového využití.\n\n"
            f"- **Celkem stažení**: {total_downloads:,}\n"
            f"- **Celkem zhlédnutí**: {total_views:,}\n"
            f"- **Celkové využití**: {total_usage:,}"
        )

    # 3) které podcasty / pořady jsou celkově nejsilnější
    by_podcast = (
        df.groupby("PodcastName", dropna=False)[["Downloads", "Zhlédnutí", "TotalUsage"]]
        .sum()
        .sort_values("TotalUsage", ascending=False)
        .reset_index()
    )
    st.markdown("**Výkon podle podcastu / pořadu:**")
    st.dataframe(by_podcast, use_container_width=True)


def main():
    st.set_page_config(page_title="Analýza online obsahu (RedCircle + YouTube)", layout="wide")
    st.title("Analýza využití online obsahu (RedCircle + YouTube)")
    st.caption(
        "Data: `data/MKP Studio - statistika.csv` – sloučená data z RedCircle a YouTube."
    )

    try:
        df = load_data()
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

    render_overview(filtered)

    col1, col2 = st.columns(2)
    with col1:
        chart_top_episodes(filtered)
    with col2:
        chart_downloads_vs_views(filtered)

    monthly_yt = load_monthly_yt()
    chart_time_trend(filtered, monthly_yt)
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


