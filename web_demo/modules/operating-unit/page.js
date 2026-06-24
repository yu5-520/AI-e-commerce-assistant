(function () {
  const s = (value) => AppShell.escape(value);
  const operationTabs = [
    ["business-products", "商品"],
    ["business-competitors", "竞品"],
    ["business-listing", "上新"],
    ["business-traffic", "流量"],
  ];
  function hero(title, side = "经营") { return `<section class="unit-hero"><div><h2>${s(title)}</h2></div><div class="unit-hero-side"><strong>${s(side)}</strong></div></section>`; }
  function metricCard(item) { return `<article class="card unit-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`; }
  function agentCard(item) { return `<article class="unit-store-row"><strong>${s(item.name)}</strong><span>${s(item.status)}</span><em>${s(item.basis)}</em></article>`; }
  function tabs() { return `<section class="page-section"><div class="section-header"><h3>经营模块</h3></div><div class="quick-actions">${operationTabs.map(([route, label]) => `<button data-operation-route="${s(route)}">${s(label)}</button>`).join("")}</div></section>`; }
  window.OperatingUnitPage = {
    route: "operating-unit",
    title: "经营",
    async render() {
      const payload = await AppApi.operatingUnit();
      if (!payload?.hasData) return `${hero("暂无数据", "数据驱动")}${tabs()}`;
      const metrics = payload.metrics || [];
      const agents = payload.agents || [];
      return `${hero(payload.unitName || "经营", payload.latestDataVersion || "已导入")}
        ${tabs()}
        <section class="kpi-grid unit-metrics">${metrics.map(metricCard).join("")}</section>
        <section class="page-section unit-store-section"><div class="section-header"><h3>经营分析</h3></div><div class="unit-store-table">${agents.map(agentCard).join("")}</div></section>`;
    },
    mount(ctx) { ctx.delegate("[data-operation-route]", "click", (_event, target) => AppRouter.navigate(target.dataset.operationRoute)); },
  };
})();
