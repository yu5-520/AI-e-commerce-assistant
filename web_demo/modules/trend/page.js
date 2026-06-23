(function () {
  const s = (value) => AppShell.escape(value ?? "");
  const riskClass = (value) => value === "高" ? "danger" : value === "中" ? "warning" : "good";

  function metrics(data) {
    const summary = data?.summary || {};
    const risk = data?.riskTaskSummary || {};
    const budget = data?.permissionBudgetSummary || {};
    const approval = data?.approvalLifecycleSummary || {};
    return `<section class="kpi-grid report-metrics">${[
      ["商品快照", summary.snapshotCount || 0, "导入生成"],
      ["风险任务", risk.total || 0, "V6.7"],
      ["额度校验", risk.budgetCheckedCount || budget.checkCount || 0, `${budget.limitCount || 0}类角色`],
      ["审批流", approval.total || 0, `待审 ${approval.byStatus?.pending_approval || 0}`],
    ].map(([a, b, c]) => AppShell.metricCard(a, b, c)).join("")}</section>`;
  }

  function budgetBlock(data) {
    const budget = data?.permissionBudgetSummary || {};
    const limits = budget.limits || [];
    return `<section class="page-section report-section"><div class="section-header"><div><h3>权限额度与审批链路</h3><p>高风险通过门控后，也只能按账号额度生成申请或升级审批。</p></div></div><div class="version-alert-list">${limits.length ? limits.map((item) => `<article class="version-alert-row"><strong>${s(item.roleName)}</strong><span>投放 ${s(item.maxAdBudgetApply)} · 采购 ${s(item.maxStockPurchaseApply)}</span><small>${s((item.approvalChain || []).join(" → ") || "无需上级审批")}</small></article>`).join("") : `<div class="log-empty">暂无额度规则。</div>`}</div></section>`;
  }

  function approvalActions(flow, context = {}) {
    if (flow.status !== "pending_approval") return `<span class="status-badge">已处理</span>`;
    if (!context.canApprove && !context.canReject) return `<span class="status-badge warning">等待 ${s(flow.currentStage || "上级")}</span>`;
    return `<button type="button" data-approve-flow="${s(flow.flowId)}">通过</button><button type="button" data-reject-flow="${s(flow.flowId)}">驳回</button>`;
  }

  function approvalBlock(data) {
    const approval = data?.approvalLifecycleSummary || {};
    const context = data?.approvalActionContext || {};
    const flows = approval.latestFlows || [];
    return `<section class="page-section report-section"><div class="section-header"><div><h3>审批生命周期</h3><p>运营申请 → 总管审批 → 老板审批 → 通过后生成执行任务。</p></div><div class="report-meta"><span>待审 ${s(approval.byStatus?.pending_approval || 0)}</span><span>通过 ${s(approval.byStatus?.approved || 0)}</span><span>驳回 ${s(approval.byStatus?.rejected || 0)}</span></div></div><div class="report-card-list">${flows.length ? flows.map((flow) => `<article class="report-card"><div><h3>${s(flow.productId)} · ${s(flow.status)}</h3><p>${s(flow.currentStage ? `当前审批：${flow.currentStage}` : "审批链路完成或无需审批")}</p><div class="report-meta"><span class="status-badge ${flow.status === "approved" ? "good" : flow.status === "rejected" ? "danger" : "warning"}">${s(flow.status)}</span><span>${s((flow.approvalChain || []).join(" → ") || "无链路")}</span><span>${s(flow.executionTaskId || "未生成执行任务")}</span></div></div><div class="report-actions">${approvalActions(flow, context)}</div></article>`).join("") : `<div class="log-empty">暂无审批流。生成需要审批的风险任务后会出现。</div>`}</div></section>`;
  }

  function riskTasks(data) {
    const plans = data?.riskTaskSummary?.latestPlans || [];
    return `<section class="page-section report-section"><div class="section-header"><h3>风险分级任务</h3><span class="status-badge">${plans.length}</span></div><div class="report-card-list">${plans.length ? plans.map((plan) => { const task = plan.payload?.task || {}; const budget = task.permissionBudgetGate || plan.payload?.permissionBudgetGate || {}; return `<article class="report-card"><div><h3>${s(task.title || plan.taskType)}</h3><p>${s(plan.productId)} · ${s(task.riskDomain || "趋势")}</p><div class="report-meta"><span class="status-badge ${riskClass(plan.riskLevel)}">${s(plan.riskLevel)}风险</span><span>${s(budget.status || "待校验")}</span><span>${s(task.suggestedTotalBudget || budget.suggestedTotalBudget || 0)}元</span></div><p>${s((task.executionRequirements || [task.riskPolicy?.rule || "任务已生成"])[0])}</p></div><div class="report-actions"><button type="button" data-open-task="${s(plan.taskId)}">查看待办</button></div></article>`; }).join("") : `<div class="log-empty">暂无风险任务。导入同商品多次报表后生成。</div>`}</div></section>`;
  }

  async function approveFlow(flowId) {
    await AppApi.post(`/api/trends/approval-flows/${encodeURIComponent(flowId)}/approve`, null, { note: "前端审批通过" });
    AppRouter.schedule("approval-approved");
  }

  async function rejectFlow(flowId) {
    const note = window.prompt("驳回原因", "指标或额度不满足当前审批要求");
    if (note === null) return;
    await AppApi.post(`/api/trends/approval-flows/${encodeURIComponent(flowId)}/reject`, null, { note });
    AppRouter.schedule("approval-rejected");
  }

  window.TrendCenterPage = {
    route: "trend-center",
    title: "趋势中心",
    async render() {
      const data = await AppApi.trendCenter(50);
      return `<section class="report-hero report-hero-clean"><div><p class="eyebrow">TREND CENTER · V6.7</p><h2>动态数据趋势中心</h2></div><div class="report-hero-side"><span>当前阶段</span><strong>审批中心操作</strong><small>前端通过 / 驳回</small></div></section>${metrics(data)}${budgetBlock(data)}${approvalBlock(data)}${riskTasks(data)}`;
    },
    mount(ctx) {
      ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask));
      ctx.delegate("[data-approve-flow]", "click", (_, node) => approveFlow(node.dataset.approveFlow));
      ctx.delegate("[data-reject-flow]", "click", (_, node) => rejectFlow(node.dataset.rejectFlow));
    }
  };
})();