(function () {
  const s = (value) => AppShell.escape(value ?? "-");

  async function loadSnapshots(type) {
    const query = new URLSearchParams({ limit: "200" });
    if (type) query.set("object_type", type);
    const response = await fetch(`/api/architecture/v8/weight-snapshots?${query.toString()}`, { method: "GET", headers: { Accept: "application/json", "X-Mock-User-Id": AppApi.getCurrentUserId() } });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  async function generateSnapshots() {
    const result = await AppApi.post("/api/architecture/v8/weight-snapshots/generate", null, {});
    window.alert(`生成权重快照 ${result.createdCount || 0} 条`);
    AppRouter.schedule("weight-snapshots-generated");
  }

  function metric(label, value, note) { return AppShell.metricCard(label, value, note || "V8.0"); }

  function typeName(type) {
    return { product: "商品", store: "店铺", operator: "运营" }[type] || type;
  }

  function compactMetrics(metrics = {}) {
    return Object.entries(metrics).slice(0, 6).map(([key, value]) => `${key}: ${typeof value === "number" ? Number(value).toFixed(3).replace(/\.000$/, "") : value}`).join(" · ");
  }

  function snapshotCard(item) {
    const tag = item.dimensions?.storeRoleTag || item.dimensions?.weightScope || item.objectType;
    return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)}</h3><p>${s(typeName(item.objectType))} · ${s(item.objectId)} · ${s(tag)}</p><div class="report-meta"><span class="status-badge">${s(item.snapshotVersion)}</span><span>${s(item.parentType)}: ${s(item.parentId)}</span></div><p>${s(compactMetrics(item.metrics))}</p></div><div class="report-actions"><span class="status-badge">只记录快照</span></div></article>`;
  }

  function countBlock(title, data = {}) {
    const rows = Object.entries(data);
    return `<section class="page-section report-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${rows.length}</span></div><div class="version-alert-list">${rows.map(([key, value]) => `<article class="version-alert-row"><strong>${s(typeName(key))}</strong><span>${s(value)}</span><small>权重快照对象</small></article>`).join("") || `<div class="log-empty">暂无数据。</div>`}</div></section>`;
  }

  window.WeightCenterPage = {
    route: "weight-center",
    title: "权重中心",
    async render() {
      const data = await loadSnapshots();
      const snapshots = data?.snapshots || [];
      return `<section class="report-hero report-hero-clean"><div><p class="eyebrow">WEIGHT CENTER · V8.0</p><h2>权重指标快照</h2></div><div class="report-hero-side"><span>当前阶段</span><strong>商品 / 店铺 / 运营</strong><small>只建快照，不生成任务</small></div></section>
      <section class="kpi-grid report-metrics">${metric("快照数", data?.snapshotCount || 0, "snapshots")}${metric("商品", data?.counts?.product || 0, "product")}${metric("店铺", data?.counts?.store || 0, "store")}${metric("运营", data?.counts?.operator || 0, "operator")}</section>
      <section class="report-preview-grid">${countBlock("对象类型", data?.counts || {})}<section class="page-section report-section"><div class="section-header"><h3>版本</h3><span class="status-badge">V8.0</span></div><div class="version-alert-list"><article class="version-alert-row"><strong>${s(data?.latestSnapshotVersion || "未生成")}</strong><span>权重快照版本</span><small>下一步 V8.1 才做环比/同比计算</small></article></div></section></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>权重快照列表</h3><p>先统一商品、店铺、运营三类对象的指标口径，为 V8.1 周期比较和 V8.6 交叉验证打底。</p></div><div class="report-actions"><button type="button" data-generate-weight>生成快照</button><button type="button" data-filter-weight="product">商品</button><button type="button" data-filter-weight="store">店铺</button><button type="button" data-filter-weight="operator">运营</button><button type="button" data-filter-weight="">全部</button></div></div><div class="report-card-list">${snapshots.map(snapshotCard).join("") || `<div class="log-empty">暂无权重快照。点击生成快照。</div>`}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-generate-weight]", "click", () => generateSnapshots());
      ctx.delegate("[data-filter-weight]", "click", async (_, node) => {
        const data = await loadSnapshots(node.dataset.filterWeight || "");
        document.querySelector(".report-card-list").innerHTML = (data.snapshots || []).map(snapshotCard).join("") || `<div class="log-empty">当前筛选暂无快照。</div>`;
      });
    },
  };
})();