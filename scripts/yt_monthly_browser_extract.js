// YouTube Studio – měsíční extrakce (2× spuštění: DESC, pak ASC)
//
// Příprava:
//   Analytics → rozšířený režim → MKP Studio → Od začátku → Měsíční → Video
//   Řazení sestupně (URL obsahuje ANALYTICS_ORDER_DIRECTION_DESC)
//
// 1. spuštění na DESC → stáhne yt_monthly_desc_raw.json
// 2. Vyčistěte konzoli (Cmd+K), ve STEJNÉ záložce přepněte řazení na vzestupné
//    (klik na sloupec Zhlédnutí), po načtení tabulky skript znovu → yt_monthly_asc_raw.json
//
// Oba JSON přesuňte do data/ a spusťte: python3 scripts/update_all.py
//
// NIKDY neotevírejte ASC v novém okně — localStorage by se ztratilo.
// Když je konzole zahlcená: Cmd+K (Clear), klikněte do řádku dole, vložte skript, Enter.

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
    baseParams +
    "&o_direction=ANALYTICS_ORDER_DIRECTION_DESC";
  const ascUrl =
    `https://studio.youtube.com/channel/${CHANNEL_ID}/analytics/tab-overview/period-default/explore?` +
    baseParams +
    "&o_direction=ANALYTICS_ORDER_DIRECTION_ASC";

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // Safari často blokuje druhé rychlé stažení — delší pauza + jeden soubor najednou
  const downloadJson = async (filename, data) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    await sleep(2500);
  };

  const waitTable = async (maxSec = 40) => {
    for (let i = 0; i < maxSec * 2; i++) {
      const table = document.querySelector("yta-explore-table");
      const tl = document.querySelector("yta-explore-timeline");
      const n =
        table?.data?.tables?.[0]?.dimensionColumn?.entityDimensionCells?.length || 0;
      if (n >= 50 && tl?.get) return { table, tl, n };
      await sleep(500);
    }
    throw new Error(
      "Tabulka se nenačetla (≥50 videí). Zkontrolujte filtr MKP Studio, Od začátku, Měsíční."
    );
  };

  const extractCurrentSort = async () => {
    const { table, tl, n } = await waitTable();
    const videos = table.data.tables[0].dimensionColumn.entityDimensionCells.map(
      (c) => ({ id: c.id, title: c.title })
    );
    const titleToId = Object.fromEntries(videos.map((v) => [v.title, v.id]));
    const rows = [...document.querySelectorAll("yta-explore-table-row")].slice(1);
    const getCb = (row) => row.querySelector("[role=checkbox]");

    const parseSeries = (s) => {
      const m = (s.name || "").match(/EXTERNAL_VIEWS_([^_]+)/);
      const vidFromName = m ? m[1] : "";
      const title =
        (s.data || []).find((p) => p.hovercardInfo?.entityTitle)?.hovercardInfo
          ?.entityTitle || "";
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
      "Neznámé řazení. Otevřete DESC stránku (sestupně podle Zhlédnutí):\n" + descUrl
    );
    return;
  }

  console.log("YouTube měsíční extrakce – běží… (≈2 min). Nechejte záložku otevřenou.");
  const result = await extractCurrentSort();
  console.log(
    `Extrahováno ${result.points.length} bodů, ${result.uniqueTitles} videí, součet ${result.sumViews}`
  );

  if (isDesc) {
    localStorage.setItem(LS_KEY, JSON.stringify(result.points));
    await downloadJson("yt_monthly_desc_raw.json", result.points);
    console.clear();
    console.log(
      "%c=== KROK 1/2 HOTOV (DESC) ===",
      "font-size:14px;font-weight:bold;color:#0a0"
    );
    console.log(
      "1. Uložte yt_monthly_desc_raw.json (Downloads).\n" +
        "2. Vyčistěte konzoli: Cmd+K (nebo ikona koše).\n" +
        "3. Ve STEJNÉ záložce přepněte řazení na vzestupné:\n" +
        "   klikněte na sloupec „Zhlédnutí“ (šipka nahoru), NEBO vložte do adresního řádku:\n" +
        ascUrl +
        "\n   (Enter ve STEJNÉ záložce — ne nové okno)\n" +
        "4. Po načtení tabulky: Cmd+K → klik do řádku konzole → vložte skript → Enter.\n" +
        "5. Stáhne se yt_monthly_asc_raw.json."
    );
    return;
  }

  // ASC
  const descRaw = JSON.parse(localStorage.getItem(LS_KEY) || "[]");
  if (!descRaw.length) {
    console.error(
      "Chybí DESC data v localStorage (pravděpodobně jste ASC otevřeli v novém okně).\n" +
        "Vraťte se na DESC ve stejné záložce a spusťte skript znovu:\n" +
        descUrl
    );
    return;
  }

  await downloadJson("yt_monthly_asc_raw.json", result.points);
  localStorage.removeItem(LS_KEY);

  console.log(
    "\n=== KROK 2/2 HOTOV ===\n" +
      `ASC: ${result.points.length} bodů (DESC už máte z kroku 1)\n` +
      "Přesuňte oba soubory do data/:\n" +
      "  yt_monthly_desc_raw.json\n" +
      "  yt_monthly_asc_raw.json\n" +
      "Pak: python3 scripts/update_all.py"
  );
})();
