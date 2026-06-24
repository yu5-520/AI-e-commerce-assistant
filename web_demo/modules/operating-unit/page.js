(function () {
  const s = (value) => AppShell.escape(value ?? "");
  const operationTabs = [
    ["business-products", "商品"],
    ["business-competitors", "竞品"],
    ["business-listing", "上新"],
    ["business-traffic", "流量"],
  ];

  function hero(title, syncState = {}) {
    const side = syncState?.label || "数据已同步";
    return `<section class="unit-hero operating-hero"><div><h2>${s(title)}</h2></div><div class="unit-hero-side"><strong>${s(side)}</strong></div></section>`;
  }

  function metricCard(item) {
    return `<article class="card unit-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`;
  }

  function tabs() {
    return `<section class="page-section operating-module-section"><div class="section-header"><h3>经营模块</h3></div><div class="quick-actions">${operationTabs.map(([route, label]) => `<button data-operation-route="${s(route)}">${s(label)}</button>`).join("")}</div></section>`;
  }

  function tagCard(item) {
    const tags = Array.isArray(item.tags) ? item.tags : [];
    return `<article class="operating-tag-card ${s(item.level || "watch")}"><span>${s(item.label)}</span><strong>${s(item.value)}</strong><div class="tag-row">${tags.map((tag) => `<em>${s(tag)}</em>`).join("")}</div></article>`;
  }

  function judgmentCard(judgment) {
    if (!judgment) return "";
    return `<section class="page-section operating-judgment-section"><div class="section-header"><h3>${s(judgment.title || "经营判断")}</h3><span class="status-badge">经营标签</span></div><article class="operating-judgment-card"><strong>${s(judgment.mainRisk || "常规观察")}</strong><p>${s(judgment.summary || "等待下一轮数据同步。")}</p></article></section>`;
  }

  window.OperatingUnitPage = {
    route: "operating-unit",
    title: "经营",
    async render() {
      const payload = await AppApi.operatingUnit();
      if (!payload?.hasData) return `${hero("暂无数据", payload?.syncState || { label: "等待数据" })}${tabs()}`;
      const metrics = (payload.metrics || []).slice(0, 4);
      const storeTags = payload.storeTags || [];
      return `${hero(payload.unitName || "经营单元", payload.syncState)}
        ${tabs()}
        <section class="kpi-grid unit-metrics operating-metrics">${metrics.map(metricCard).join("")}</section>
        <section class="page-section unit-store-section operating-tag-section"><div class="section-header"><h3>店铺经营标签</h3><span class="status-badge">自动判断</span></div><div class="operating-tag-grid">${storeTags.map(tagCard).join("")}</div></section>
        ${judgmentCard(payload.operatingJudgment)}`;
    },
    mount(ctx) { ctx.delegate("[data-operation-route]", "click", (_event, target) => AppRouter.navigate(target.dataset.operationRoute)); },
  };
})();