(function () {
  const s = (value) => AppShell.escape(value ?? "-");

  async function loadSnapshots(type) {
    const query = new URLSearchParams({ limit: "200" });
    if (type) query.set("object_type", type);
    const response = await fetch(`/api/architecture/v8/weight-snapshots?${query.toString()}`, { method: "GET", headers: { Accept: "application/json", "X-Mock-User-Id": AppApi.getCurrentUserId() } });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  async function loadComparisons(type, comparisonType) {
    const query = new URLSearchParams({ limit: "240" });
    if (type) query.set("object_type", type);
    if (comparisonType) query.set("comparison_type", comparisonType);
    const response = await fetch(`/api/architecture/v8/weight-comparisons?${query.toString()}`, { method: "GET", headers: { Accept: "application/json", "X-Mock-User-Id": AppApi.getCurrentUserId() } });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  async function loadRagHits(type, status) {
    const query = new URLSearchParams({ limit: "240" });
    if (type) query.set("object_type", type);
    if (status) query.set("hit_status", status);
    const response = await fetch(`/api/architecture/v8/weight-rag-hits?${query.toString()}`, { method: "GET", headers: { Accept: "application/json", "X-Mock-User-Id": AppApi.getCurrentUserId() } });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  async function loadRelations(type, risk) {
    const query = new URLSearchParams({ limit: "240" });
    if (type) query.set("object_type", type);
    if (risk) query.set("risk_direction", risk);
    const response = await fetch(`/api/architecture/v8/linked-relations?${query.toString()}`, { method: "GET", headers: { Accept: "application/json", "X-Mock-User-Id": AppApi.getCurrentUserId() } });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  async function generateSnapshots() { const result = await AppApi.post("/api/architecture/v8/weight-snapshots/generate", null, {}); window.alert(`生成权重快照 ${result.createdCount || 0} 条`); AppRouter.schedule("weight-snapshots-generated"); }
  async function generateComparisons() { const result = await AppApi.post("/api/architecture/v8/weight-comparisons/generate", null, {}); window.alert(`生成周期比较 ${result.createdCount || 0} 条`); AppRouter.schedule("weight-comparisons-generated"); }
  async function generateRagHits() { const result = await AppApi.post("/api/architecture/v8/weight-rag-hits/generate", null, {}); window.alert(`生成标准线命中 ${result.createdCount || 0} 条`); AppRouter.schedule("weight-rag-generated"); }
  async function generateRelations() { const result = await AppApi.post("/api/architecture/v8/linked-relations/generate", null, {}); window.alert(`生成联动关系 ${result.createdCount || 0} 条`); AppRouter.schedule("linked-relations-generated"); }

  function metric(label, value, note) { return AppShell.metricCard(label, value, note || "V8.3"); }
  function typeName(type) { return { product: "商品", store: "店铺", operator: "运营" }[type] || type; }
  function comparisonName(type) { return { period_over_period: "环比", multi_period_average: "多周期均值", volatility: "波动率", year_over_year: "同比" }[type] || type; }
  function directionName(direction) { return { up: "上升", down: "下降", stable: "稳定", insufficient_reference: "样本不足" }[direction] || direction; }
  function hitStatusName(status) { return { below_standard: "低于标准线", above_risk_line: "高于风险线", within_standard: "达标" }[status] || status; }
  function riskName(value) { return { positive: "正向", neutral: "中性", negative: "负向" }[value] || value; }
  function compactMetrics(metrics = {}) { return Object.entries(metrics).slice(0, 6).map(([key, value]) => `${key}: ${typeof value === "number" ? Number(value).toFixed(3).replace(/\.000$/, "") : value}`).join(" · "); }
  function pct(value) { return value === null || value === undefined ? "-" : `${(Number(value) * 100).toFixed(1)}%`; }

  function snapshotCard(item) { const tag = item.dimensions?.storeRoleTag || item.dimensions?.weightScope || item.objectType; return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)}</h3><p>${s(typeName(item.objectType))} · ${s(item.objectId)} · ${s(tag)}</p><div class="report-meta"><span class="status-badge">${s(item.snapshotVersion)}</span><span>${s(item.parentType)}: ${s(item.parentId)}</span></div><p>${s(compactMetrics(item.metrics))}</p></div><div class="report-actions"><span class="status-badge">快照</span></div></article>`; }
  function comparisonCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.metricLabel || item.metricName)}</h3><p>${s(typeName(item.objectType))} · ${s(comparisonName(item.comparisonType))} · ${s(directionName(item.direction))}</p><div class="report-meta"><span class="status-badge">${s(item.confidence)}</span><span>当前 ${s(item.currentValue)}</span><span>参考 ${s(item.referenceValue)}</span><span>变化 ${s(pct(item.changeRate))}</span></div><p>V8.1 只解释波动，不生成升降权任务。</p></div><div class="report-actions"><span class="status-badge">${s(item.comparisonId)}</span></div></article>`; }
  function ragHitCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.metricLabel || item.metricName)}</h3><p>${s(typeName(item.objectType))} · ${s(hitStatusName(item.hitStatus))} · ${s(item.domain)}</p><div class="report-meta"><span class="status-badge">${s(item.severity)}</span><span>当前 ${s(item.currentValue)}</span><span>标准 ${s(item.operator === "min" ? "≥" : "≤")} ${s(item.standardLine)}</span><span>连续 ${s(item.consecutiveLowCount)}</span></div><p>${s(item.payload?.summary || "V8.2 只判断标准线命中，不生成任务。")}</p></div><div class="report-actions"><span class="status-badge">${s(item.ruleId)}</span></div></article>`; }
  function relationCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.relationName)}</h3><p>${s(typeName(item.objectType))} · ${s(riskName(item.riskDirection))} · ${s(item.confidence)}</p><div class="report-meta"><span class="status-badge">${s(item.relationType)}</span><span>证据 ${s(item.evidenceCount)}</span><span>${s((item.metricKeys || []).join(" / "))}</span></div><p>${s(item.conclusion)}</p></div><div class="report-actions"><span class="status-badge">联动解释</span></div></article>`; }

  function countBlock(title, data = {}, labeler = (v) => v) { const rows = Object.entries(data); return `<section class="page-section report-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${rows.length}</span></div><div class="version-alert-list">${rows.map(([key, value]) => `<article class="version-alert-row"><strong>${s(labeler(key))}</strong><span>${s(value)}</span><small>V8.3 指标</small></article>`).join("") || `<div class="log-empty">暂无数据。</div>`}</div></section>`; }

  window.WeightCenterPage = {
    route: "weight-center",
    title: "权重中心",
    async render() {
      const data = await loadSnapshots();
      const comparison = await loadComparisons();
      const rag = await loadRagHits();
      const relation = await loadRelations();
      const snapshots = data?.snapshots || [];
      const comparisons = comparison?.comparisons || [];
      const hits = rag?.hits || [];
      const relations = relation?.relations || [];
      return `<section class="report-hero report-hero-clean"><div><p class="eyebrow">WEIGHT CENTER · V8.3</p><h2>权重联动比对</h2></div><div class="report-hero-side"><span>当前阶段</span><strong>快照 / 周期 / 标准线 / 联动</strong><small>仍不生成升降权任务</small></div></section>
      <section class="kpi-grid report-metrics">${metric("快照数", data?.snapshotCount || 0, "snapshots")}${metric("比较数", comparison?.comparisonCount || 0, "comparisons")}${metric("标准命中", rag?.hitCount || 0, "rag")}${metric("联动关系", relation?.relationCount || 0, "relations")}</section>
      <section class="report-preview-grid">${countBlock("联动方向", relation?.byRiskDirection || {}, riskName)}${countBlock("联动对象", relation?.byObjectType || {}, typeName)}${countBlock("标准线状态", rag?.byHitStatus || {}, hitStatusName)}</section>
      <section class="page-section report-section"><div class="section-header"><div><h3>联动关系</h3><p>V8.3 把周期变化、RAG 标准线和多指标组合起来解释波动方向；V8.4 才做评分。</p></div><div class="report-actions"><button type="button" data-generate-relation>生成联动</button><button type="button" data-filter-relation="negative">负向</button><button type="button" data-filter-relation="neutral">中性</button><button type="button" data-filter-relation="positive">正向</button><button type="button" data-filter-relation="">全部</button></div></div><div class="relation-card-list report-card-list">${relations.map(relationCard).join("") || `<div class="log-empty">暂无联动关系。先生成快照、比较、标准线，再生成联动。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>RAG 标准线命中</h3><p>V8.2 判断商品、店铺、运营指标是否达标。</p></div><div class="report-actions"><button type="button" data-generate-rag>生成标准线</button><button type="button" data-filter-rag="below_standard">低于标准线</button><button type="button" data-filter-rag="above_risk_line">高于风险线</button><button type="button" data-filter-rag="within_standard">达标</button><button type="button" data-filter-rag="">全部</button></div></div><div class="rag-card-list report-card-list">${hits.map(ragHitCard).join("") || `<div class="log-empty">暂无标准线命中。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>周期比较列表</h3><p>V8.1 计算环比、多周期均值、波动率和可用同比。</p></div><div class="report-actions"><button type="button" data-generate-comparison>生成比较</button><button type="button" data-filter-comparison="period_over_period">环比</button><button type="button" data-filter-comparison="multi_period_average">均值</button><button type="button" data-filter-comparison="volatility">波动率</button><button type="button" data-filter-comparison="">全部</button></div></div><div class="comparison-card-list report-card-list">${comparisons.map(comparisonCard).join("") || `<div class="log-empty">暂无周期比较。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>权重快照列表</h3><p>商品、店铺、运营三类对象的统一指标口径。</p></div><div class="report-actions"><button type="button" data-generate-weight>生成快照</button><button type="button" data-filter-weight="product">商品</button><button type="button" data-filter-weight="store">店铺</button><button type="button" data-filter-weight="operator">运营</button><button type="button" data-filter-weight="">全部</button></div></div><div class="snapshot-card-list report-card-list">${snapshots.map(snapshotCard).join("") || `<div class="log-empty">暂无权重快照。</div>`}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-generate-weight]", "click", () => generateSnapshots());
      ctx.delegate("[data-generate-comparison]", "click", () => generateComparisons());
      ctx.delegate("[data-generate-rag]", "click", () => generateRagHits());
      ctx.delegate("[data-generate-relation]", "click", () => generateRelations());
      ctx.delegate("[data-filter-weight]", "click", async (_, node) => { const data = await loadSnapshots(node.dataset.filterWeight || ""); document.querySelector(".snapshot-card-list").innerHTML = (data.snapshots || []).map(snapshotCard).join("") || `<div class="log-empty">当前筛选暂无快照。</div>`; });
      ctx.delegate("[data-filter-comparison]", "click", async (_, node) => { const data = await loadComparisons("", node.dataset.filterComparison || ""); document.querySelector(".comparison-card-list").innerHTML = (data.comparisons || []).map(comparisonCard).join("") || `<div class="log-empty">当前筛选暂无比较。</div>`; });
      ctx.delegate("[data-filter-rag]", "click", async (_, node) => { const data = await loadRagHits("", node.dataset.filterRag || ""); document.querySelector(".rag-card-list").innerHTML = (data.hits || []).map(ragHitCard).join("") || `<div class="log-empty">当前筛选暂无标准线命中。</div>`; });
      ctx.delegate("[data-filter-relation]", "click", async (_, node) => { const data = await loadRelations("", node.dataset.filterRelation || ""); document.querySelector(".relation-card-list").innerHTML = (data.relations || []).map(relationCard).join("") || `<div class="log-empty">当前筛选暂无联动关系。</div>`; });
    },
  };
})();