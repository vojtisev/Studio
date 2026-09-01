// Spusťte v DevTools Console na stránce Red Circle:
// Stats → Downloads → Episode Performance, Select Date Range + Month
(() => {
  const rootEl = document.querySelector("#root");
  const fiberKey = Object.keys(rootEl).find(
    (k) => k.startsWith("__reactContainer") || k.startsWith("__reactFiber")
  );
  let fiber = rootEl[fiberKey],
    store = null,
    hops = 0;
  while (fiber && hops < 100) {
    const p = fiber.memoizedProps || fiber.pendingProps;
    if (p && p.store && p.store.getState) {
      store = p.store;
      break;
    }
    fiber = fiber.child || fiber.return;
    hops++;
  }
  if (!store) throw new Error("Redux store not found");

  const st = store.getState();
  const key = Object.keys(st.stats.stats).find(
    (k) => k.includes("Episode-Performance-All Podcasts") && k.endsWith("-Month")
  );
  if (!key) throw new Error("Monthly Episode Performance key not found");
  const rows = st.stats.stats[key] || [];

  const showTitle = {};
  for (const [sid, meta] of Object.entries(st.shows.shows || {})) {
    showTitle[sid] = meta.title || meta.name || "";
  }

  const epMeta = {};
  for (const [sid, bag] of Object.entries(st.episodesByShow || {})) {
    if (!bag || !bag.episodes) continue;
    const eps = bag.episodes;
    const epMap = eps.uuid ? { [eps.uuid]: eps } : eps;
    for (const [eid, ep] of Object.entries(epMap)) {
      if (!ep || typeof ep !== "object") continue;
      const uuid = ep.uuid || eid;
      epMeta[uuid] = {
        title: ep.title || "",
        showUUID: sid,
        podcast: showTitle[sid] || "",
      };
    }
  }

  const esc = (s) => `"${String(s ?? "").replace(/"/g, '""')}"`;
  const lines = [
    "PodcastName,Epizoda,EpisodeUUID,Měsíc,RedCircle_Downloads,PodcastUUID",
  ];
  let total = 0;
  for (const r of rows) {
    const pv = r.pathValues || [];
    const month = String(pv[0] || "").slice(0, 7);
    const epUUID = pv[1] || "";
    const count = Number(r.count) || 0;
    if (!month || !epUUID) continue;
    total += count;
    const meta = epMeta[epUUID] || { title: epUUID, showUUID: "", podcast: "" };
    lines.push(
      [
        esc(meta.podcast),
        esc(meta.title),
        esc(epUUID),
        esc(month),
        count,
        esc(meta.showUUID),
      ].join(",")
    );
  }

  const blob = new Blob(["\ufeff" + lines.join("\n")], {
    type: "text/csv;charset=utf-8",
  });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "MKP Studio - Red Circle měsíčně.csv";
  a.click();
  console.log(
    `RC monthly extract OK: ${lines.length - 1} rows, total downloads ${total}, key=${key}`
  );
})();
