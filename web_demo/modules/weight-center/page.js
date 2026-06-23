(function () {
  const s = (value) => AppShell.escape(value ?? "-");

  async function fetchJson(path) {
    const response = await fetch(path, { method: "GET", headers: { Accept: "application/json", "X-Mock-User-Id": AppApi.getCurrentUserId() } });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  async function loadSnapshots(type) { const q = new URLSearchParams({ limit: "160" }); if (type) q.set("object_type", type); return fetchJson(`/api/architecture/v8/weight-snapshots?${q.toString()}`); }
  async function loadComparisons(type, comparisonType) { const q = new URLSearchParams({ limit: "180" }); if (type) q.set("object_type", type); if (comparisonType) q.set("comparison_type", comparisonType); return fetchJson(`/api/architecture/v8/weight-comparisons?${q.toString()}`); }
  async function loadRagHits(type, status) { const q = new URLSearchParams({ limit: "180" }); if (type) q.set("object_type", type); if (status) q.set("hit_status", status); return fetchJson(`/api/architecture/v8/weight-rag-hits?${q.toString()}`); }
  async function loadRelations(type, risk) { const q = new URLSearchParams({ limit: "180" }); if (type) q.set("object_type", type); if (risk) q.set("risk_direction", risk); return fetchJson(`/api/architecture/v8/linked-relations?${q.toString()}`); }
  async function loadScores(type, state) { const q = new URLSearchParams({ limit: "180" }); if (type) q.set("object_type", type); if (state) q.set("weight_state", state); return fetchJson(`/api/architecture/v8/weight-scores?${q.toString()}`); }
  async function loadContext(type, intensity) { const q = new URLSearchParams({ limit: "180" }); if (type) q.set("object_type", type); if (intensity) q.set("task_intensity_level", intensity); return fetchJson(`/api/architecture/v8/context-weights?${q.toString()}`); }
  async function loadCross(type, status) { const q = new URLSearchParams({ limit: "180" }); if (type) q.set("object_type", type); if (status) q.set("validation_status", status); return fetchJson(`/api/architecture/v8/cross-validations?${q.toString()}`); }
  async function loadGroups(type, status) { const q = new URLSearchParams({ limit: "180" }); if (type) q.set("object_type", type); if (status) q.set("group_status", status); return fetchJson(`/api/architecture/v8/weight-task-groups?${q.toString()}`); }

  async function postAndRefresh(path, label) { const result = await AppApi.post(path, null, {}); window.alert(`生成${label} ${result.createdCount || 0} 条`); AppRouter.schedule(`${label}-generated`); }
  const generateSnapshots = () => postAndRefresh("/api/architecture/v8/weight-snapshots/generate", "权重快照");
  const generateComparisons = () => postAndRefresh("/api/architecture/v8/weight-comparisons/generate", "周期比较");
  const generateRagHits = () => postAndRefresh("/api/architecture/v8/weight-rag-hits/generate", "标准线命中");
  const generateRelations = () => postAndRefresh("/api/architecture/v8/linked-relations/generate", "联动关系");
  const generateScores = () => postAndRefresh("/api/architecture/v8/weight-scores/generate", "权重评分");
  const generateContext = () => postAndRefresh("/api/architecture/v8/context-weights/generate", "上下文修正");
  const generateCross = () => postAndRefresh("/api/architecture/v8/cross-validations/generate", "交叉验证");
  const generateGroups = () => postAndRefresh("/api/architecture/v8/weight-task-groups/generate", "权重任务组");

  function metric(label, value, note) { return AppShell.metricCard(label, value, note || "V8.7"); }
  function typeName(type) { return { product: "商品", store: "店铺", operator: "运营" }[type] || type; }
  function stateName(value) { return { promote_candidate: "升权候选", maintain: "维持", observe: "观察", repair: "修复", test_repair: "测试修复", demote_candidate: "降权候选", hard_demote_candidate: "强降权候选", stop_loss_review: "止损复核", expand_candidate: "扩权候选", resource_limit_candidate: "限制资源候选", demotion_review: "降权复核", manager_intervention: "总管介入", promotion_suggestion: "升权建议", coaching_observe: "辅导观察", permission_adjustment_review: "权限调整复核" }[value] || value; }
  function intensityName(value) { return { L1: "观察", L2: "修复", L3: "降权候选", L4: "强降权候选", L5: "止损复核", H1: "人工复核依据", H2: "辅导观察", H3: "权限调整复核" }[value] || value; }
  function validationName(value) { return { confirmed: "交叉确认", protected_confirmed: "保护型确认", conflict: "存在冲突", buffered: "缓冲观察", needs_review: "需要复核", human_review_only: "仅人工复核", insufficient_evidence: "证据不足" }[value] || value; }
  function readinessName(value) { return { ready_for_task_group: "可进任务组候选", not_ready: "暂不进入", human_review_only: "仅人工复核" }[value] || value; }
  function groupStatusName(value) { return { pending_approval: "待审批", evidence_review: "证据复核", human_review_draft: "人工复核草案" }[value] || value; }
  function hitStatusName(status) { return { below_standard: "低于标准线", above_risk_line: "高于风险线", within_standard: "达标" }[status] || status; }
  function directionName(direction) { return { up: "上升", down: "下降", stable: "稳定", insufficient_reference: "样本不足", positive: "正向", neutral: "中性", negative: "负向" }[direction] || direction; }
  function comparisonName(type) { return { period_over_period: "环比", multi_period_average: "多周期均值", volatility: "波动率", year_over_year: "同比" }[type] || type; }
  function compactMetrics(metrics = {}) { return Object.entries(metrics).slice(0, 6).map(([key, value]) => `${key}: ${typeof value === "number" ? Number(value).toFixed(3).replace(/\.000$/, "") : value}`).join(" · "); }
  function pct(value) { return value === null || value === undefined ? "-" : `${(Number(value) * 100).toFixed(1)}%`; }

  function countBlock(title, data = {}, labeler = (v) => v) {
    const rows = Object.entries(data);
    return `<section class="page-section report-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${rows.length}</span></div><div class="version-alert-list">${rows.map(([key, value]) => `<article class="version-alert-row"><strong>${s(labeler(key))}</strong><span>${s(value)}</span><small>V8.7 指标</small></article>`).join("") || `<div class="log-empty">暂无数据。</div>`}</div></section>`;
  }

  function taskGroupCard(item) {
    const firstTasks = (item.tasks || []).slice(0, 3).map((task) => `<li>${s(task.title)}：${s(task.action)}</li>`).join("");
    return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.groupName)}</h3><p>${s(typeName(item.objectType))} · ${s(groupStatusName(item.groupStatus))} · ${s(item.priority)} · 审批：${s(item.approvalRole)}</p><div class="report-meta"><span class="status-badge">${s(item.finalIntensityLevel)}</span><span>任务 ${s(item.taskCount)}</span><span>${s(readinessName(item.readiness))}</span><span>${s(validationName(item.validationStatus))}</span></div><ul>${firstTasks}</ul><p>V8.7 只生成任务组草案，V8.8 审批前不得执行。</p></div><div class="report-actions"><span class="status-badge">任务组</span></div></article>`;
  }
  function crossCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.validationLabel || validationName(item.validationStatus))}</h3><p>${s(typeName(item.objectType))} · ${s(readinessName(item.readiness))} · ${s(item.confidence)}</p><div class="report-meta"><span class="status-badge">${s(item.finalIntensityLabel || intensityName(item.finalIntensityLevel))}</span><span>证据 ${s(item.evidenceCount)}</span><span>冲突 ${s(item.conflictCount)}</span><span>分数 ${s(item.crossScore)}</span></div><p>${s(item.conclusion)}</p></div><div class="report-actions"><span class="status-badge">交叉验证</span></div></article>`; }
  function contextCard(item) { const factors = item.contextFactors || {}; return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.adjustedLabel || stateName(item.adjustedState))}</h3><p>${s(typeName(item.objectType))} · ${s(item.contextType)} · ${s(item.taskIntensityLabel || intensityName(item.taskIntensityLevel))}</p><div class="report-meta"><span class="status-badge">${s(item.taskIntensityLevel)}</span><span>基础 ${s(item.baseScore)}</span><span>修正 ${s(item.adjustedScore)}</span><span>${s(factors.storeRoleTag || factors.assignedStoreCount || "context")}</span></div><p>${s(item.contextSummary)}</p></div><div class="report-actions"><span class="status-badge">上下文修正</span></div></article>`; }
  function scoreCard(item) { const calc = item.payload?.calculation || {}; return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.stateLabel || stateName(item.weightState))}</h3><p>${s(typeName(item.objectType))} · 分数 ${s(item.weightScore)} · ${s(item.riskLevel)}风险</p><div class="report-meta"><span class="status-badge">${s(item.weightState)}</span><span>正向 ${s(item.positiveCount)}</span><span>负向 ${s(item.negativeCount)}</span><span>证据 ${s(item.evidenceCount)}</span></div><p>联动 ${s(calc.relationDelta)} · 标准线 ${s(calc.hitDelta)} · 周期 ${s(calc.comparisonDelta)}</p></div><div class="report-actions"><span class="status-badge">评分</span></div></article>`; }
  function relationCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.relationName)}</h3><p>${s(typeName(item.objectType))} · ${s(directionName(item.riskDirection))} · ${s(item.confidence)}</p><div class="report-meta"><span class="status-badge">${s(item.relationType)}</span><span>证据 ${s(item.evidenceCount)}</span><span>${s((item.metricKeys || []).join(" / "))}</span></div><p>${s(item.conclusion)}</p></div><div class="report-actions"><span class="status-badge">联动解释</span></div></article>`; }
  function ragHitCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.metricLabel || item.metricName)}</h3><p>${s(typeName(item.objectType))} · ${s(hitStatusName(item.hitStatus))} · ${s(item.domain)}</p><div class="report-meta"><span class="status-badge">${s(item.severity)}</span><span>当前 ${s(item.currentValue)}</span><span>标准 ${s(item.operator === "min" ? "≥" : "≤")} ${s(item.standardLine)}</span><span>连续 ${s(item.consecutiveLowCount)}</span></div><p>${s(item.payload?.summary || "标准线命中")}</p></div><div class="report-actions"><span class="status-badge">${s(item.ruleId)}</span></div></article>`; }
  function comparisonCard(item) { return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)} · ${s(item.metricLabel || item.metricName)}</h3><p>${s(typeName(item.objectType))} · ${s(comparisonName(item.comparisonType))} · ${s(directionName(item.direction))}</p><div class="report-meta"><span class="status-badge">${s(item.confidence)}</span><span>当前 ${s(item.currentValue)}</span><span>参考 ${s(item.referenceValue)}</span><span>变化 ${s(pct(item.changeRate))}</span></div></div><div class="report-actions"><span class="status-badge">${s(item.comparisonId)}</span></div></article>`; }
  function snapshotCard(item) { const tag = item.dimensions?.storeRoleTag || item.dimensions?.weightScope || item.objectType; return `<article class="report-card"><div><h3>${s(item.objectName || item.objectId)}</h3><p>${s(typeName(item.objectType))} · ${s(item.objectId)} · ${s(tag)}</p><div class="report-meta"><span class="status-badge">${s(item.snapshotVersion)}</span><span>${s(item.parentType)}: ${s(item.parentId)}</span></div><p>${s(compactMetrics(item.metrics))}</p></div><div class="report-actions"><span class="status-badge">快照</span></div></article>`; }

  window.WeightCenterPage = {
    route: "weight-center",
    title: "权重中心",
    async render() {
      const data = await loadSnapshots();
      const comparison = await loadComparisons();
      const rag = await loadRagHits();
      const relation = await loadRelations();
      const score = await loadScores();
      const context = await loadContext();
      const cross = await loadCross();
      const groups = await loadGroups();
      const snapshots = data?.snapshots || [];
      const comparisons = comparison?.comparisons || [];
      const hits = rag?.hits || [];
      const relations = relation?.relations || [];
      const scores = score?.scores || [];
      const adjustments = context?.adjustments || [];
      const validations = cross?.validations || [];
      const taskGroups = groups?.taskGroups || [];
      return `<section class="report-hero report-hero-clean"><div><p class="eyebrow">WEIGHT CENTER · V8.7</p><h2>交叉任务组</h2></div><div class="report-hero-side"><span>当前阶段</span><strong>验证结果 → 任务组草案</strong><small>审批前不得执行</small></div></section>
      <section class="kpi-grid report-metrics">${metric("任务组", groups?.taskGroupCount || 0, "groups")}${metric("待审批", groups?.byGroupStatus?.pending_approval || 0, "approval")}${metric("证据复核", groups?.byGroupStatus?.evidence_review || 0, "review")}${metric("人工复核", groups?.byGroupStatus?.human_review_draft || 0, "human")}</section>
      <section class="report-preview-grid">${countBlock("任务组状态", groups?.byGroupStatus || {}, groupStatusName)}${countBlock("优先级", groups?.byPriority || {})}${countBlock("对象类型", groups?.byObjectType || {}, typeName)}</section>
      <section class="page-section report-section"><div class="section-header"><div><h3>交叉任务组</h3><p>V8.7 根据交叉验证生成任务组草案，V8.8 审批通过前不得执行。</p></div><div class="report-actions"><button type="button" data-generate-group>生成任务组</button><button type="button" data-filter-group="pending_approval">待审批</button><button type="button" data-filter-group="evidence_review">证据复核</button><button type="button" data-filter-group="human_review_draft">人工复核</button><button type="button" data-filter-group="">全部</button></div></div><div class="group-card-list report-card-list">${taskGroups.map(taskGroupCard).join("") || `<div class="log-empty">暂无任务组。先生成交叉验证，再生成任务组。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>交叉验证</h3><p>V8.6 判断是否可进入任务组候选。</p></div><div class="report-actions"><button type="button" data-generate-cross>生成验证</button><button type="button" data-filter-cross="confirmed">确认</button><button type="button" data-filter-cross="conflict">冲突</button><button type="button" data-filter-cross="buffered">缓冲</button><button type="button" data-filter-cross="">全部</button></div></div><div class="cross-card-list report-card-list">${validations.map(crossCard).join("") || `<div class="log-empty">暂无交叉验证。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>上下文修正</h3></div><div class="report-actions"><button type="button" data-generate-context>生成修正</button><button type="button" data-filter-context="product">商品</button><button type="button" data-filter-context="store">店铺</button><button type="button" data-filter-context="operator">运营</button><button type="button" data-filter-context="">全部</button></div></div><div class="context-card-list report-card-list">${adjustments.map(contextCard).join("") || `<div class="log-empty">暂无上下文修正。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>权重评分</h3></div><div class="report-actions"><button type="button" data-generate-score>生成评分</button><button type="button" data-filter-score="product">商品</button><button type="button" data-filter-score="store">店铺</button><button type="button" data-filter-score="operator">运营</button><button type="button" data-filter-score="">全部</button></div></div><div class="score-card-list report-card-list">${scores.map(scoreCard).join("") || `<div class="log-empty">暂无评分。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>联动关系</h3></div><div class="report-actions"><button type="button" data-generate-relation>生成联动</button><button type="button" data-filter-relation="negative">负向</button><button type="button" data-filter-relation="neutral">中性</button><button type="button" data-filter-relation="positive">正向</button><button type="button" data-filter-relation="">全部</button></div></div><div class="relation-card-list report-card-list">${relations.map(relationCard).join("") || `<div class="log-empty">暂无联动关系。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>RAG 标准线命中</h3></div><div class="report-actions"><button type="button" data-generate-rag>生成标准线</button><button type="button" data-filter-rag="below_standard">低于标准线</button><button type="button" data-filter-rag="above_risk_line">高于风险线</button><button type="button" data-filter-rag="within_standard">达标</button><button type="button" data-filter-rag="">全部</button></div></div><div class="rag-card-list report-card-list">${hits.map(ragHitCard).join("") || `<div class="log-empty">暂无标准线命中。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>周期比较</h3></div><div class="report-actions"><button type="button" data-generate-comparison>生成比较</button><button type="button" data-filter-comparison="period_over_period">环比</button><button type="button" data-filter-comparison="multi_period_average">均值</button><button type="button" data-filter-comparison="volatility">波动率</button><button type="button" data-filter-comparison="">全部</button></div></div><div class="comparison-card-list report-card-list">${comparisons.map(comparisonCard).join("") || `<div class="log-empty">暂无周期比较。</div>`}</div></section>
      <section class="page-section report-section"><div class="section-header"><div><h3>权重快照</h3></div><div class="report-actions"><button type="button" data-generate-weight>生成快照</button><button type="button" data-filter-weight="product">商品</button><button type="button" data-filter-weight="store">店铺</button><button type="button" data-filter-weight="operator">运营</button><button type="button" data-filter-weight="">全部</button></div></div><div class="snapshot-card-list report-card-list">${snapshots.map(snapshotCard).join("") || `<div class="log-empty">暂无权重快照。</div>`}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-generate-weight]", "click", () => generateSnapshots());
      ctx.delegate("[data-generate-comparison]", "click", () => generateComparisons());
      ctx.delegate("[data-generate-rag]", "click", () => generateRagHits());
      ctx.delegate("[data-generate-relation]", "click", () => generateRelations());
      ctx.delegate("[data-generate-score]", "click", () => generateScores());
      ctx.delegate("[data-generate-context]", "click", () => generateContext());
      ctx.delegate("[data-generate-cross]", "click", () => generateCross());
      ctx.delegate("[data-generate-group]", "click", () => generateGroups());
      ctx.delegate("[data-filter-group]", "click", async (_, node) => { const data = await loadGroups("", node.dataset.filterGroup || ""); document.querySelector(".group-card-list").innerHTML = (data.taskGroups || []).map(taskGroupCard).join("") || `<div class="log-empty">当前筛选暂无任务组。</div>`; });
      ctx.delegate("[data-filter-cross]", "click", async (_, node) => { const data = await loadCross("", node.dataset.filterCross || ""); document.querySelector(".cross-card-list").innerHTML = (data.validations || []).map(crossCard).join("") || `<div class="log-empty">当前筛选暂无交叉验证。</div>`; });
      ctx.delegate("[data-filter-context]", "click", async (_, node) => { const data = await loadContext(node.dataset.filterContext || ""); document.querySelector(".context-card-list").innerHTML = (data.adjustments || []).map(contextCard).join("") || `<div class="log-empty">当前筛选暂无修正。</div>`; });
      ctx.delegate("[data-filter-score]", "click", async (_, node) => { const data = await loadScores(node.dataset.filterScore || ""); document.querySelector(".score-card-list").innerHTML = (data.scores || []).map(scoreCard).join("") || `<div class="log-empty">当前筛选暂无评分。</div>`; });
      ctx.delegate("[data-filter-weight]", "click", async (_, node) => { const data = await loadSnapshots(node.dataset.filterWeight || ""); document.querySelector(".snapshot-card-list").innerHTML = (data.snapshots || []).map(snapshotCard).join("") || `<div class="log-empty">当前筛选暂无快照。</div>`; });
      ctx.delegate("[data-filter-comparison]", "click", async (_, node) => { const data = await loadComparisons("", node.dataset.filterComparison || ""); document.querySelector(".comparison-card-list").innerHTML = (data.comparisons || []).map(comparisonCard).join("") || `<div class="log-empty">当前筛选暂无比较。</div>`; });
      ctx.delegate("[data-filter-rag]", "click", async (_, node) => { const data = await loadRagHits("", node.dataset.filterRag || ""); document.querySelector(".rag-card-list").innerHTML = (data.hits || []).map(ragHitCard).join("") || `<div class="log-empty">当前筛选暂无标准线命中。</div>`; });
      ctx.delegate("[data-filter-relation]", "click", async (_, node) => { const data = await loadRelations("", node.dataset.filterRelation || ""); document.querySelector(".relation-card-list").innerHTML = (data.relations || []).map(relationCard).join("") || `<div class="log-empty">当前筛选暂无联动关系。</div>`; });
    },
  };
})();