(function () {
  const s = (value) => AppShell.escape(value ?? "");
  const operationTabs = [
    ["product", "商品", "商品预警与处理任务"],
    ["competitor", "竞品", "竞品信号与测试任务"],
    ["listing", "上新", "上新验证与增长任务"],
    ["traffic", "流量", "流量趋势与放量任务"],
  ];

  function hero(title, syncState = {}) {
    const side = syncState?.label || "数据已同步";
    return `<section class="unit-hero operating-hero"><div><h2>${s(title)}</h2></div><div class="unit-hero-side"><strong>${s(side)}</strong></div></section>`;
  }

  function metricCard(item) {
    return `<article class="card unit-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`;
  }

  function tabs() {
    return `<section class="page-section operating-module-section"><div class="section-header"><h3>经营模块</h3><span class="status-badge">任务统一承接</span></div><div class="quick-actions">${operationTabs.map(([module, label, desc]) => `<button data-operation-module="${s(module)}"><strong>${s(label)}</strong><span>${s(desc)}</span></button>`).join("")}</div></section>`;
  }

  function tagList(tags) {
    const items = Array.isArray(tags) && tags.length ? tags : ["—"];
    return `<div class="store-row-tags">${items.map((tag) => `<em>${s(tag)}</em>`).join("")}</div>`;
  }

  function storeRow(row) {
    return `<article class="operating-store-row ${s(row.level || "watch")}">
      <div class="store-row-main"><strong>${s(row.storeName || row.storeId || "店铺")}</strong><span>${s(row.platform || "平台")} · 商品 ${s(row.productCount ?? 0)}</span></div>
      <div><span>店铺权重</span>${tagList([row.storeWeightTag || "常规店铺"])}</div>
      <div><span>商品结构</span>${tagList(row.productRoleTags)}</div>
      <div><span>风险标签</span>${tagList(row.riskTags)}</div>
      <div><span>任务强度</span>${tagList([row.taskIntensity || "常规处理", `预警 ${row.alertCount ?? 0}`])}</div>
      <button type="button" class="secondary" data-store-task="${s(row.storeId || "")}">查看任务</button>
    </article>`;
  }

  function judgmentCard(judgment) {
    if (!judgment) return "";
    return `<section class="page-section operating-judgment-section"><div class="section-header"><h3>${s(judgment.title || "经营判断")}</h3><span class="status-badge">店铺标签</span></div><article class="operating-judgment-card"><strong>${s(judgment.mainRisk || "常规观察")}</strong><p>${s(judgment.summary || "等待下一轮数据同步。")}</p></article></section>`;
  }

  window.OperatingUnitPage = {
    route: "operating-unit",
    title: "经营",
    async render() {
      const payload = await AppApi.operatingUnit();
      if (!payload?.hasData) return `${hero("暂无数据", payload?.syncState || { label: "等待数据" })}${tabs()}`;
      const metrics = (payload.metrics || []).slice(0, 4);
      const storeRows = payload.storeRows || [];
      return `${hero(payload.unitName || "经营单元", payload.syncState)}
        ${tabs()}
        <section class="kpi-grid unit-metrics operating-metrics">${metrics.map(metricCard).join("")}</section>
        <section class="page-section unit-store-section operating-store-section"><div class="section-header"><h3>店铺经营状态</h3><span class="status-badge">一店一行</span></div><div class="operating-store-list">${storeRows.map(storeRow).join("")}</div></section>
        ${judgmentCard(payload.operatingJudgment)}`;
    },
    mount(ctx) {
      ctx.delegate("[data-operation-module]", "click", (_event, target) => AppRouter.navigate("business-actions", { moduleFilter: target.dataset.operationModule }));
      ctx.delegate("[data-store-task]", "click", (_event, target) => AppRouter.navigate("business-actions", { storeId: target.dataset.storeTask }));
    },
  };
})();