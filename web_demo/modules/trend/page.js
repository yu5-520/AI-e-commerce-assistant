(function () {
  let trendData = null;
  const s = (value) => AppShell.escape(value ?? "");
  const pct = (value) => {
    const number = Number(value || 0);
    if (!Number.isFinite(number)) return "-";
    return `${number > 0 ? "+" : ""}${(number * 100).toFixed(1)}%`;
  };
  const num = (value) => {
    const number = Number(value || 0);
    if (!Number.isFinite(number)) return s(value || "-");
    return Number.isInteger(number) ? String(number) : number.toFixed(2);
  };
  const directionText = (value) => value === "up" ? "上涨" : value === "down" ? "下滑" : "稳定";
  const riskClass = (value) => value === "高" ? "danger" : value === "中" ? "warning" : "good";

  function metricCards(summary = {}, riskSummary = {}, indicatorSummary = {}, gateSummary = {}) {
    return `<section class="kpi-grid report-metrics">${[
      ["商品快照", summary.snapshotCount || 0, "导入后生成"],
      ["风险任务", riskSummary.total || 0, "V6.4 生成"],
      ["RAG命中", riskSummary.ragMatchedCount || 0, `${indicatorSummary.ruleCount || 0} 条规则`],
      ["投产申请", riskSummary.investmentApplicationAllowedCount || 0, `门控通过 ${gateSummary.byStatus?.passed || 0}`]
    ].map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section>`;
  }

  function compactList(title, items = []) {
    return `<article class="page-section report-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${s(items.length)} 项</span></div><div class="version-alert-list">${items.length ? items.map((item) => `<article class="version-alert-row"><strong>${s(item.name)}</strong><span>${s(item.count)} 个商品 / 快照</span><small>基于当前账号可见范围</small></article>`).join("") : `<div class="log-empty">暂无数据，导入两次以上同商品报表后会形成趋势。</div>`}</div></article>`;
  }

  function indicatorRulesBlock(summary = {}) {
    const rules = summary.rules || [];
    const matches = summary.latestMatches || [];
    return `<section class="page-section report-section"><div class="section-header"><div><h3>RAG 指标规则</h3><p>中高风险任务必须命中公司规则，不能由 Agent 自造比例。</p></div><span class="status-badge">${s(summary.ruleCount || 0)} 条</span></div><div class="report-preview-grid"><article><h4>规则库</h4><div class="version-alert-list">${rules.length ? rules.slice(0, 6).map((rule) => `<article class="version-alert-row"><strong>${s(rule.ruleName)}</strong><span>${s(rule.domain)} · ${s(rule.riskLevel)}风险 · ${s(rule.sourceTitle)}</span><small>${s(rule.formula)}</small></article>`).join("") : `<div class="log-empty">暂无 RAG 指标规则。</div>`}</div></article><article><h4>最近命中</h4><div class="version-alert-list">${matches.length ? matches.slice(0, 6).map((match) => `<article class="version-alert-row"><strong>${s(match.productId || "商品")}</strong><span>${s(match.domain)} · ${s(match.riskLevel)}风险 · ${s(match.status)}</span><small>${s((match.constraints?.executionLines || []).join(" / "))}</small></article>`).join("") : `<div class="log-empty">暂无指标命中。生成风险任务后会出现。</div>`}</div></article></div></section>`;
  }

  function highRiskGateBlock(summary = {}) {
    const gates = summary.latestGates || [];
    return `<section class="page-section report-section"><div class="section-header"><div><h3>高风险趋势门控</h3><p>加库存、加投放、打造爆品必须至少 4 项指标稳定向好，且没有硬阻断。</p></div><div class="report-meta"><span>通过 ${s(summary.byStatus?.passed || 0)}</span><span>阻断 ${s(summary.byStatus?.blocked || 0)}</span></div></div><div class="report-card-list">${gates.length ? gates.slice(0, 8).map((gate) => `<article class="report-card"><div><h3>${s(gate.productId)} · ${gate.applicationAllowed ? "可申请" : "仅复核"}</h3><p>${s(gate.decision)}</p><div class="report-meta"><span class="status-badge ${gate.applicationAllowed ? "good" : "warning"}">${s(gate.gateStatus)}</span><span>向好 ${s(gate.positiveMetricCount)}/${s(gate.requiredPositiveMetricCount)}</span><span>阻断 ${s(gate.blockerCount)}</span></div><small>${s((gate.positiveMetrics || []).map((item) => item.metricLabel || item.metricName).join(" / "))}</small></div><div class="report-actions"><span class="status-badge">V6.4</span></div></article>`).join("") : `<div class="log-empty">暂无高风险门控记录。生成高风险申请或复核任务后会出现。</div>`}</div></section>`;
  }

  function productList(items = []) {
    return `<section class="page-section report-section"><div class="section-header"><h3>单商品趋势对象</h3><span class="status-badge">${s(items.length)} 个</span></div><div class="report-card-list">${items.length ? items.map((item) => `<article class="report-card"><div><h3>${s(item.title || item.productId || item.product_id)}</h3><p>${s(item.platform || "未知平台")} · ${s(item.category || "未分类")}</p><div class="report-meta"><span>${s(item.productId || item.product_id)}</span><span>${s(item.storeName || item.storeId || "未绑定店铺")}</span><span>快照 ${s(item.snapshotCount || 0)}</span></div></div><div class="report-actions"><span class="status-badge">趋势对象</span></div></article>`).join("") : `<div class="log-empty">暂无商品快照。请先在报表中心导入包含商品 ID 的 ERP / CRM 数据。</div>`}</div></section>`;
  }

  function trendList(items = []) {
    return `<section class="page-section report-section"><div class="section-header"><h3>最新指标趋势</h3><span class="status-badge">${s(items.length)} 条</span></div><div class="version-alert-list">${items.length ? items.map((item) => `<article class="version-alert-row"><strong>${s(item.productId)} · ${s(item.metricLabel || item.metricName)}</strong><span>${s(directionText(item.trendDirection))} · ${num(item.previousValue)} → ${num(item.currentValue)} · ${pct(item.changeRate)}</span><small>${s(item.datasetName || "报表")} · ${s(item.dataVersion || "")}</small></article>`).join("") : `<div class="log-empty">同一商品至少导入两次后，系统会计算指标变化。</div>`}</div></section>`;
  }

  function signalList(items = []) {
    return `<section class="page-section report-section"><div class="section-header"><h3>经营信号</h3><span class="status-badge">${s(items.length)} 条</span></div><div class="report-card-list">${items.length ? items.map((item) => `<article class="report-card"><div><h3>${s(item.signalType)}</h3><p>${s(item.productId)} · ${s(item.metricLabel || item.sourceMetric)} · ${s(directionText(item.trendDirection))}</p><div class="report-meta"><span class="status-badge ${riskClass(item.riskLevel)}">${s(item.riskLevel)}风险</span><span>${s(item.taskCandidate ? "任务候选" : "观察信号")}</span><span>${pct(item.changeRate)}</span></div><p>${s(item.reason || "趋势中心记录该信号，并由 V6.4 高风险趋势门控生成任务。")}</p></div><div class="report-actions"><span class="status-badge">V6.4</span></div></article>`).join("") : `<div class="log-empty">暂无经营信号。导入新的同商品数据后会自动生成。</div>`}</div></section>`;
  }

  function riskTaskList(summary = {}) {
    const plans = summary.latestPlans || [];
    const levels = summary.byLevel || {};
    return `<section class="page-section report-section"><div class="section-header"><div><h3>风险分级任务</h3><p>低风险可直接观察；中风险带 RAG 指标；高风险通过趋势门控后只生成申请/审批任务。</p></div><div class="report-meta"><span>高 ${s(levels["高"] || 0)}</span><span>中 ${s(levels["中"] || 0)}</span><span>低 ${s(levels["低"] || 0)}</span></div></div><div class="report-card-list">${plans.length ? plans.map((plan) => { const task = plan.payload?.task || {}; const gate = task.highRiskTrendGate || plan.payload?.highRiskTrendGate || {}; const constraints = task.ragIndicatorConstraints || plan.payload?.indicatorConstraints || {}; return `<article class="report-card"><div><h3>${s(task.title || plan.taskType)}</h3><p>${s(plan.productId)} · ${s(task.riskDomain || "趋势")} · ${s(task.deadline || "待定")}</p><div class="report-meta"><span class="status-badge ${riskClass(plan.riskLevel)}">${s(plan.riskLevel)}风险</span><span>${s(task.investmentApplicationAllowed ? "可申请" : constraints.status === "matched" ? "RAG已命中" : "待复核")}</span><span>${s(gate.gateStatus || "-")}</span></div><p>${s((task.executionRequirements || constraints.executionLines || [task.riskPolicy?.rule || "风险分级任务已进入任务池。"])[0])}</p></div><div class="report-actions"><button type="button" data-open-task="${s(plan.taskId)}">查看待办</button></div></article>`; }).join("") : `<div class="log-empty">暂无风险分级任务。导入同一商品的第二份报表并形成信号后，系统会生成任务。</div>`}</div></section>`;
  }

  window.TrendCenterPage = {
    route: "trend-center",
    title: "趋势中心",
    async render() {
      trendData = await AppApi.trendCenter(50);
      const summary = trendData?.summary || {};
      const riskSummary = trendData?.riskTaskSummary || {};
      const indicatorSummary = trendData?.indicatorRuleSummary || {};
      const gateSummary = trendData?.highRiskGateSummary || {};
      return `<section class="report-hero report-hero-clean"><div><p class="eyebrow">TREND CENTER · V6.4</p><h2>动态数据趋势中心</h2></div><div class="report-hero-side"><span>当前阶段</span><strong>高风险趋势门控</strong><small>V6.5 接权限额度审批</small></div></section>${metricCards(summary, riskSummary, indicatorSummary, gateSummary)}<section class="report-preview-grid">${compactList("总店铺趋势", trendData?.storeTrends || [])}${compactList("平台趋势", trendData?.platformTrends || [])}${compactList("平台类目趋势", trendData?.categoryTrends || [])}</section>${indicatorRulesBlock(indicatorSummary)}${highRiskGateBlock(gateSummary)}${riskTaskList(riskSummary)}${productList(trendData?.latestProducts || [])}${trendList(trendData?.latestTrends || [])}${signalList(trendData?.latestSignals || [])}`;
    },
    mount(ctx) {
      ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask));
      ctx.onRefresh = async () => {
        trendData = await AppApi.trendCenter(50);
        AppRouter.schedule("trend-refresh");
      };
    }
  };
})();