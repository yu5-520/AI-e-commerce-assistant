(function () {
  const s = (value) => AppShell.escape(value ?? "");
  const riskClass = (value) => value === "高" ? "danger" : value === "中" ? "warning" : "good";

  function metrics(data) {
    const summary = data?.summary || {};
    const risk = data?.riskTaskSummary || {};
    const budget = data?.permissionBudgetSummary || {};
    return `<section class="kpi-grid report-metrics">${[
      ["商品快照", summary.snapshotCount || 0, "导入生成"],
      ["风险任务", risk.total || 0, "V6.5"],
      ["投产申请", risk.investmentApplicationAllowedCount || 0, "需审批"],
      ["额度校验", risk.budgetCheckedCount || budget.checkCount || 0, `${budget.limitCount || 0}类角色`],
    ].map(([a, b, c]) => AppShell.metricCard(a, b, c)).join("")}</section>`;
  }

  function budgetBlock(data) {
    const budget = data?.permissionBudgetSummary || {};
    const limits = budget.limits || [];
    const checks = budget.latestChecks || [];
    return `<section class="page-section report-section"><div class="section-header"><div><h3>权限额度与审批链路</h3><p>高风险通过门控后，也只能按账号额度生成申请或升级审批。</p></div></div><div class="report-preview-grid"><article><h4>角色额度</h4><div class="version-alert-list">${limits.length ? limits.map((item) => `<article class="version-alert-row"><strong>${s(item.roleName)}</strong><span>投放 ${s(item.maxAdBudgetApply)} · 采购 ${s(item.maxStockPurchaseApply)}</span><small>${s((item.approvalChain || []).join(" → ") || "无需上级审批")}</small></article>`).join("") : `<div class="log-empty">暂无额度规则。</div>`}</div></article><article><h4>最近校验</h4><div class="version-alert-list">${checks.length ? checks.slice(0, 8).map((item) => `<article class="version-alert-row"><strong>${s(item.productId || "商品")}</strong><span>${s(item.status)} · ${s(item.requesterRoleId)} · ${s(item.suggestedTotalBudget || 0)}元</span><small>${s((item.approvalChain || []).join(" → ") || "无需审批")}</small></article>`).join("") : `<div class="log-empty">生成 V6.5 风险任务后会出现额度校验。</div>`}</div></article></div></section>`;
  }

  function riskTasks(data) {
    const plans = data?.riskTaskSummary?.latestPlans || [];
    return `<section class="page-section report-section"><div class="section-header"><h3>风险分级任务</h3><span class="status-badge">${plans.length}</span></div><div class="report-card-list">${plans.length ? plans.map((plan) => { const task = plan.payload?.task || {}; const budget = task.permissionBudgetGate || plan.payload?.permissionBudgetGate || {}; return `<article class="report-card"><div><h3>${s(task.title || plan.taskType)}</h3><p>${s(plan.productId)} · ${s(task.riskDomain || "趋势")}</p><div class="report-meta"><span class="status-badge ${riskClass(plan.riskLevel)}">${s(plan.riskLevel)}风险</span><span>${s(budget.status || "待校验")}</span><span>${s(task.suggestedTotalBudget || budget.suggestedTotalBudget || 0)}元</span></div><p>${s((task.executionRequirements || [task.riskPolicy?.rule || "任务已生成"])[0])}</p></div><div class="report-actions"><button type="button" data-open-task="${s(plan.taskId)}">查看待办</button></div></article>`; }).join("") : `<div class="log-empty">暂无风险任务。导入同商品多次报表后生成。</div>`}</div></section>`;
  }

  window.TrendCenterPage = {
    route: "trend-center",
    title: "趋势中心",
    async render() {
      const data = await AppApi.trendCenter(50);
      window.__trendData = data;
      return `<section class="report-hero report-hero-clean"><div><p class="eyebrow">TREND CENTER · V6.5</p><h2>动态数据趋势中心</h2></div><div class="report-hero-side"><span>当前阶段</span><strong>权限额度审批</strong><small>高风险只生成申请/审批</small></div></section>${metrics(data)}${budgetBlock(data)}${riskTasks(data)}`;
    },
    mount(ctx) {
      ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask));
    }
  };
})();