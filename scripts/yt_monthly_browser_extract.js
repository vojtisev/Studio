// YouTube Studio – měsíční extrakce (2× spuštění: DESC, pak ASC)
//
// Příprava (jednou za aktualizaci):
//   Analytics → rozšířený režim → entita MKP Studio → Od začátku → Měsíční → Obsah = Video
//   URL musí obsahovat o_direction=ANALYTICS_ORDER_DIRECTION_DESC (seřazeno sestupně podle Zhlédnutí)
//
// 1. spuštění na DESC stránce → uloží data do localStorage, vypíše ASC odkaz
// 2. spuštění na ASC stránce  → stáhne yt_monthly_desc_raw.json + yt_monthly_asc_raw.json
//
// Stažené JSON přesuňte do data/ a spusťte: python3 scripts/update_all.py

(async () => {
  const LS_KEY = "__ytMonthlyDescBackup";
  const CHANNEL_ID = "UCPnMb9K2vgHBgclVB5dbXdA";
  const GROUP_ID = "IctWU5gX7wE";

  const baseParams =
    `c=${CHANNEL_ID}&theme=dark&entity_type=GROUP&entity_id=${GROUP_ID}` +
    "&time_period=lifetime&explore_type=TABLE_AND_CHART&metric=EXTERNAL_VIEWS" +
    "&granularity=MONTH&t_metrics=EXTERNAL_VIEWS&dimension=VIDEO&o_column=EXTERNAL_VIEWS";

  const descUrl =
    `https://studio.youtube.com/channel/${CHANNEL_ID}/analytics/tab-overview/period-default/explore?` +
    baseParams + "&o_direction=ANALYTICS_ORDER_DIRECTION_DESC";
  const ascUrl =
    `https://studio.youtube.com/channel/${CHANNEL_ID}/analytics/tab-overview/period-default/explore?` +
    baseParams + "&o_direction=ANALYTICS_ORDER_DIRECTION_ASC";

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const downloadJson = (filename, data) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
  };

  const waitTable = async (maxSec = 40) => {
    for (let i = 0; i < maxSec * 2; i++) {
      const table = document.querySelector("yta-explore-table");
      const tl = document.querySelector("yta-explore-timeline");
      const n = table?.data?.tables?.[0]?.dimensionColumn?.entityDimensionCells?.length || 0;
      if (n >= 50 && tl?.get) return { table, tl, n };
      await sleep(500);
    }
    throw new Error(
      "Tabulka se nenačetla (potřebujeme ≥50 videí). Zkontrolujte filtr MKP Studio, období Od začátku a granularitu Měsíční."
    );
  };

  const extractCurrentSort = async () => {
    const { table, tl, n } = await waitTable();
    const videos = table.data.tables[0].dimensionColumn.entityDimensionCells.map((c) => ({
      id: c.id,
      title: c.title,
    }));
    const titleToId = Object.fromEntries(videos.map((v) => [v.title, v.id]));
    const rows = [...document.querySelectorAll("yta-explore-table-row")].slice(1);
    const getCb = (row) => row.querySelector("[role=checkbox]");

    const parseSeries = (s) => {
      const m = (s.name || "").match(/EXTERNAL_VIEWS_([^_]+)/);
      const vidFromName = m ? m[1] : "";
      const title =
        (s.data || []).find((p) => p.hovercardInfo?.entityTitle)?.hovercardInfo?.entityTitle || "";
      const id = titleToId[title] || vidFromName;
      return (s.data || [])
        .filter((p) => p.x != null && (p.y || 0) > 0)
        .map((p) => {
          const d = new Date(p.x);
          const month =
            d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
          return { vid: id, title, month, views: p.y || 0 };
        });
    };

    const uncheckAll = async () => {
      for (const row of rows) {
        const cb = getCb(row);
        if (cb && cb.getAttribute("aria-checked") === "true") {
          cb.click();
          await sleep(40);
        }
      }
      await sleep(400);
    };

    const selectBatch = async (indices) => {
      await uncheckAll();
      for (const i of indices) {
        const cb = getCb(rows[i]);
        if (cb) {
          cb.click();
          await sleep(70);
        }
      }
      await sleep(2000);
    };

    const all = [];
    for (let b = 0; b < 10; b++) {
      const batch = Array.from({ length: 5 }, (_, k) => b * 5 + k);
      await selectBatch(batch);
      const spec = tl.get("timelineChartSpec");
      for (const s of (spec && spec.seriesList) || []) {
        all.push(...parseSeries(s));
      }
    }

    const uniqueTitles = new Set(all.map((x) => x.title).filter(Boolean));
    const sumViews = all.reduce((a, x) => a + x.views, 0);
    return { points: all, tableVideos: n, uniqueTitles: uniqueTitles.size, sumViews };
  };

  const isAsc = location.href.includes("ANALYTICS_ORDER_DIRECTION_ASC");
  const isDesc = location.href.includes("ANALYTICS_ORDER_DIRECTION_DESC");

  if (!isAsc && !isDesc) {
    console.error(
      "Neznámé řazení. Otevřete nejdřív DESC URL (viz scripts/Aktualizace.md):\n" + descUrl
    );
    return;
  }

  console.log("YouTube měsíční extrakce – běží… (≈2 min)");
  const result = await extractCurrentSort();
  console.log(
    `Extrahováno ${result.points.length} bodů, ${result.uniqueTitles} videí, součet zhlédnutí ${result.sumViews}`
  );

  if (isDesc) {
    localStorage.setItem(LS_KEY, JSON.stringify(result.points));
    console.log(
      "\n=== KROK 1/2 HOTOV (DESC) ===\n" +
        "1. Otevřete ASC stránku (seřazení vzestupně):\n" +
        ascUrl +
        "\n2. Po načtení tabulky znovu vložte a spusťte tento skript.\n" +
        "3. Stáhnou se oba JSON → přesuňte do složky data/"
    );
    return;
  }

  const descRaw = JSON.parse(localStorage.getItem(LS_KEY) || "[]");
  if (!descRaw.length) {
    console.error(
      "Chybí DESC data v localStorage. Nejdřív spusťte skript na DESC stránce:\n" + descUrl
    );
    return;
  }

  downloadJson("yt_monthly_desc_raw.json", descRaw);
  await sleep(800);
  downloadJson("yt_monthly_asc_raw.json", result.points);
  localStorage.removeItem(LS_KEY);

  console.log(
    "\n=== KROK 2/2 HOTOV ===\n" +
      `DESC: ${descRaw.length} bodů, ASC: ${result.points.length} bodů\n` +
      "Přesuňte oba soubory do data/ a spusťte:\n" +
      "  python3 scripts/update_all.py"
  );
})();
