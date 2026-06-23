(function () {
  const s = (value) => AppShell.escape(value ?? "-");

  async function fetchJson(path) {
    const response = await fetch(path, { method: "GET", headers: { Accept: "application/json", "X-Mock-User-Id": AppApi.getCurrentUserId() } });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  async function loadSnapshots(type) { const q = new URLSearchParams({ limit: "200" }); if (type) q.set("object_type", type); return fetchJson(`/api/architecture/v8/weight-snapshots?${q.toString()}`); }
  async function loadComparisons(type, comparisonType) { const q = new URLSearchParams({ limit: "240" }); if (type) q.set("object_type", type); if (comparisonType) q.set("comparison_type", comparisonType); return fetchJson(`/api/architecture/v8/weight-comparisons?${q.toString()}`); }
  async function loadRagHits(type, status) { const q = new URLSearchParams({ limit: "240" }); if (type) q.set("object_type", type); if (status) q.set("hit_status", status); return fetchJson(`/api/architecture/v8/weight-rag-hits?${q.toString()}`); }
  async function loadRelations(type, risk) { const q = new URLSearchParams({ limit: "240" }); if (type) q.set("object_type", type); if (risk) q.set("risk_direction", risk); return fetchJson(`/api/architecture/v8/linked-relations?${q.toString()}`); }
  async function loadScores(type, state) { const q = new URLSearchParams({ limit: "240" }); if (type) q.set("object_type", type); if (state) q.set("weight_state", state); return fetchJson(`/api/architecture/v8/weight-scores?${q.toString()}`); }

  async function postAndRefresh(path, label) { const result = await AppApi.post(path, null, {}); window.alert(`生成${label} ${result.createdCount || 0} 条`); AppRouter.schedule(`${label}-generated`); }
  const generateSnapshots = () => postAndRefresh("/api/architecture/v8/weight-snapshots/generate", "权重快照");
  const generateComparisons = () => postAndRefresh("/api/architecture/v8/weight-comparisons/generate", "周期比较");
  const generateRagHits = () => postAndRefresh("/api/architecture/v8/weight-rag-hits/generate", "标准线命中");
  const generateRelations = () => postAndRefresh("/api/architecture/v8/linked-relations/generate", "联动关系");
  const generateScores = () => postAndRefresh("/api/architecture/v8/weight-scores/generate", "权重评分");

  function metric(label, value, note) { return AppShell.metricCard(label, value, note || "V8.4"); }
  function typeName(type) { return { product: "商品", store: "店铺", operator: "运营" }[type] || type; }
  function comparisonName(type) { return { period_over_period: "环比", multi_period_average: "多周期均值", volatility: "波动率", year_over_year: "同比" }[type] || type; }
  function directionName(direction) { return { up: "上升", down: "下降", stable: "稳定", insufficient_reference: "样本不足", positive: "正向", neutral: "中性", negative: "负向" }[direction] || direction; }
  function hitStatusName(status) { return { below_standard: "低于标准线", above_risk_line: "高于风险线", within_standard: "达标" }[status] || status; }
  function stateName(value) { return { promote_candidate: "升权候选", maintain: "维持", observe: "观察", repair: "修复", demote_candidate: "降权候选", stop_loss_review: "止损复核", expand_candidate: "扩权候选", resource_limit_candidate: "限制资源候选", demotion_review: "降权复核", manager_intervention: "总管介入", promotion_suggestion: "升权建议", coaching_observe: "辅导观察", permission_adjustment_review: "权限调整复核" }[value] || value; }
  function compactMetrics(metrics = {}) { return Object.entries(metrics).slice(0, 6).map(([key, value]) => `${key}: ${typeof value === "number" ? Number(value).toFixed(3).replace(/\.000$/, "") : value}`).join(" · "); }
  function pct(value) { return value === null || value === undefined ? "-" : `${(Number(value) * 100).toFixed(1)}%`; }

  function snapshotCard(item) { const tag = item.dimensions?.storeRoleTag || item.dimensions?.weightScope || item.objectType; return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)}</h3><p>${s(typeName(item.objectType))} · ${s(item.objectId)} · ${s(tag)}</p><div class="report-meta"><span class="status-badge">${s(item.snapshotVersion)}</span><span>${s(item.parentType)}: ${s(item.parentId)}</span></div><p>${s(compactMetrics(item.metrics))}</p></div><div class="report-actions"><span class="status-badge">快照</span></div></article>`; }
  function comparisonCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.metricLabel || item.metricName)}</h3><p>${s(typeName(item.objectType))} · ${s(comparisonName(item.comparisonType))} · ${s(directionName(item.direction))}</p><div class="report-meta"><span class="status-badge">${s(item.confidence)}</span><span>当前 ${s(item.currentValue)}</span><span>参考 ${s(item.referenceValue)}</span><span>变化 ${s(pct(item.changeRate))}</span></div><p>V8.1 只解释波动，不生成升降权任务。</p></div><div class="report-actions"><span class="status-badge">${s(item.comparisonId)}</span></div></article>`; }
  function ragHitCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.metricLabel || item.metricName)}</h3><p>${s(typeName(item.objectType))} · ${s(hitStatusName(item.hitStatus))} · ${s(item.domain)}</p><div class="report-meta"><span class="status-badge">${s(item.severity)}</span><span>当前 ${s(item.currentValue)}</span><span>标准 ${s(item.operator === "min" ? "≥" : "≤")} ${s(item.standardLine)}</span><span>连续 ${s(item.consecutiveLowCount)}</span></div><p>${s(item.payload?.summary || "V8.2 只判断标准线命中，不生成任务。")}</p></div><div class="report-actions"><span class="status-badge">${s(item.ruleId)}</span></div></article>`; }
  function relationCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.relationName)}</h3><p>${s(typeName(item.objectType))} · ${s(directionName(item.riskDirection))} · ${s(item.confidence)}</p><div class="report-meta"><span class="status-badge">${s(item.relationType)}</span><span>证据 ${s(item.evidenceCount)}</span><span>${s((item.metricKeys || []).join(" / "))}</span></div><p>${s(item.conclusion)}</p></div><div class="report-actions"><span class="status-badge">联动解释</span></div></article>`; }
  function scoreCard(item) { const calc = item.payload?.calculation || {}; return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.stateLabel || stateName(item.weightState))}</h3><p>${s(typeName(item.objectType))} · 分数 ${s(item.weightScore)} · ${s(item.riskLevel)}风险</p><div class="report-meta"><span class="status-badge">${s(item.weightState)}</span><span>正向 ${s(item.positiveCount)}</span><span>负向 ${s(item.negativeCount)}</span><span>证据 ${s(item.evidenceCount)}</span></div><p>计算：联动 ${s(calc.relationDelta)} · 标准线 ${s(calc.hitDelta)} · 周期 ${s(calc.comparisonDelta)}。V8.4 只输出状态，不生成任务。</p></div><div class="report-actions"><span class="status-badge">评分</span></div></article>`; }
  function countBlock(title, data = {}, labeler = (v) => v) { const rows = Object.entries(data); return `<section class="page-section report-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${rows.length}</span></div><div class="version-alert-list">${rows.map(([key, value]) => `<article class="version-alert-row"><strong>${s(labeler(key))}</strong><span>${s(value)}</span><small>V8.4 指标</small></article>`).join("") || `<div class="log-empty">暂无数据。</div>`}</div></section>`; }

  window.WeightCenterPage = {
    route: "weight-center",
    title: "权重中心",
    async render() {
      const data = await loadSnapshots();
      const comparison = await loadComparisons();
      const rag = await loadRagHits();
      const relation = await loadRelations();
      const score = await loadScores();
      const snapshots = data?.snapshots || [];
      const comparisons = comparison?.comparisons || [];
      const hits = rag?.hits || [];
      const relations = relation?.relations || [];
      const scores = score?.scores || [];
      return `<section class="report-hero report-hero-clean"><div><p class="eyebrow">WEIGHT CENTER · V8.4</p><h2>对象权重评分</h2></div><div class="report-hero-side"><span>当前阶段</span><strong>快照 / 周期 / 标准线 / 联动 / 评分</strong><small>仍不生成升降权任务</small></div></section>
      <section class="kpi-grid report-metrics">${metric("快照数", data?.snapshotCount || 0, "snapshots")}${metric("联动关系", relation?.relationCount || 0, "relations")}${metric("评分数", score?.scoreCount || 0, "scores")}${metric("高风险", score?.byRiskLevel?.高 || 0, "risk")}</section>
      <section class="report-preview-grid">${countBlock("权重状态", score?.byState || {}, stateName)}${countBlock("风险等级", score?.byRiskLevel || {})}${countBlock("对象类型", score?.byObjectType || {}, typeName)}</section>
      <section class="page-section report-section"><div class="section-header"><div><h3>权重评分</h3><p>V8.4 把联动、标准线和周期比较合成对象权重状态；V8.5 才做上下文修正，V8.7 才生成任务。</p></div><div class="report-actions"><button type="button" data-generate-score>生成评分</button><button type="button" data-filter-score="product">商品</button><button type="button" data-filter-score="store">店铺</button><button type="button" data-filter-score="operator">运营</button><button type="button" data-filter-score="">全部</button></div></div><div class="score-card-list report-card-list">${scores.map(scoreCard).join("") || `<div class="log-empty">暂无评分。先生成快照、比较、标准线、联动，再生成评分。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>联动关系</h3><p>V8.3 把周期变化、RAG 标准线和多指标组合起来解释波动方向。</p></div><div class="report-actions"><button type="button" data-generate-relation>生成联动</button><button type="button" data-filter-relation="negative">负向</button><button type="button" data-filter-relation="neutral">中性</button><button type="button" data-filter-relation="positive">正向</button><button type="button" data-filter-relation="">全部</button></div></div><div class="relation-card-list report-card-list">${relations.map(relationCard).join("") || `<div class="log-empty">暂无联动关系。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>RAG 标准线命中</h3><p>V8.2 判断商品、店铺、运营指标是否达标。</p></div><div class="report-actions"><button type="button" data-generate-rag>生成标准线</button><button type="button" data-filter-rag="below_standard">低于标准线</button><button type="button" data-filter-rag="above_risk_line">高于风险线</button><button type="button" data-filter-rag="within_standard">达标</button><button type="button" data-filter-rag="">全部</button></div></div><div class="rag-card-list report-card-list">${hits.map(ragHitCard).join("") || `<div class="log-empty">暂无标准线命中。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>周期比较列表</h3><p>V8.1 计算环比、多周期均值、波动率和可用同比。</p></div><div class="report-actions"><button type="button" data-generate-comparison>生成比较</button><button type="button" data-filter-comparison="period_over_period">环比</button><button type="button" data-filter-comparison="multi_period_average">均值</button><button type="button" data-filter-comparison="volatility">波动率</button><button type="button" data-filter-comparison="">全部</button></div></div><div class="comparison-card-list report-card-list">${comparisons.map(comparisonCard).join("") || `<div class="log-empty">暂无周期比较。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>权重快照列表</h3><p>商品、店铺、运营三类对象的统一指标口径。</p></div><div class="report-actions"><button type="button" data-generate-weight>生成快照</button><button type="button" data-filter-weight="product">商品</button><button type="button" data-filter-weight="store">店铺</button><button type="button" data-filter-weight="operator">运营</button><button type="button" data-filter-weight="">全部</button></div></div><div class="snapshot-card-list report-card-list">${snapshots.map(snapshotCard).join("") || `<div class="log-empty">暂无权重快照。</div>`}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-generate-weight]", "click", () => generateSnapshots());
      ctx.delegate("[data-generate-comparison]", "click", () => generateComparisons());
      ctx.delegate("[data-generate-rag]", "click", () => generateRagHits());
      ctx.delegate("[data-generate-relation]", "click", () => generateRelations());
      ctx.delegate("[data-generate-score]", "click", () => generateScores());
      ctx.delegate("[data-filter-score]", "click", async (_, node) => { const data = await loadScores(node.dataset.filterScore || ""); document.querySelector(".score-card-list").innerHTML = (data.scores || []).map(scoreCard).join("") || `<div class="log-empty">当前筛选暂无评分。</div>`; });
      ctx.delegate("[data-filter-weight]", "click", async (_, node) => { const data = await loadSnapshots(node.dataset.filterWeight || ""); document.querySelector(".snapshot-card-list").innerHTML = (data.snapshots || []).map(snapshotCard).join("") || `<div class="log-empty">当前筛选暂无快照。</div>`; });
      ctx.delegate("[data-filter-comparison]", "click", async (_, node) => { const data = await loadComparisons("", node.dataset.filterComparison || ""); document.querySelector(".comparison-card-list").innerHTML = (data.comparisons || []).map(comparisonCard).join("") || `<div class="log-empty">当前筛选暂无比较。</div>`; });
      ctx.delegate("[data-filter-rag]", "click", async (_, node) => { const data = await loadRagHits("", node.dataset.filterRag || ""); document.querySelector(".rag-card-list").innerHTML = (data.hits || []).map(ragHitCard).join("") || `<div class="log-empty">当前筛选暂无标准线命中。</div>`; });
      ctx.delegate("[data-filter-relation]", "click", async (_, node) => { const data = await loadRelations("", node.dataset.filterRelation || ""); document.querySelector(".relation-card-list").innerHTML = (data.relations || []).map(relationCard).join("") || `<div class="log-empty">当前筛选暂无联动关系。</div>`; });
    },
  };
})();