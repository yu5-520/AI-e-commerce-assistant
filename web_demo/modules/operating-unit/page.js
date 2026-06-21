(function () {
  const s = (value) => AppShell.escape(value);
  function hero(title, side = "V5") { return `<section class="unit-hero"><div><h2>${s(title)}</h2></div><div class="unit-hero-side"><strong>${s(side)}</strong></div></section>`; }
  function metricCard(item) { return `<article class="card unit-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`; }
  function agentCard(item) { return `<article class="unit-store-row"><strong>${s(item.name)}</strong><span>${s(item.status)}</span><em>${s(item.basis)}</em></article>`; }
  window.OperatingUnitPage = {
    route: "operating-unit",
    title: "经营单元",
    async render() {
      const payload = await AppApi.operatingUnit();
      if (!payload?.hasData) return `${hero("暂无数据", "数据驱动")}`;
      const metrics = payload.metrics || [];
      const agents = payload.agents || [];
      return `${hero(payload.unitName || "经营单元", payload.latestDataVersion || "已导入")}
        <section class="kpi-grid unit-metrics">${metrics.map(metricCard).join("")}</section>
        <section class="page-section unit-store-section"><div class="section-header"><h3>经营分析</h3></div><div class="unit-store-table">${agents.map(agentCard).join("")}</div></section>`;
    },
  };
})();
