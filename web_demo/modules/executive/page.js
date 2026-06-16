(function () {
  const s = (value) => AppShell.escape(value);

  function tasks() {
    return window.AppTaskStore?.listActiveTasks?.() || [];
  }

  function logs() {
    return window.AppTaskStore?.listLogs?.() || [];
  }

  function metricGrid(items) {
    return `<section class="kpi-grid report-metrics">${items.map(([a, b, c]) => AppShell.metricCard(a, b, c)).join("")}</section>`;
  }

  function cards(title, badge, items) {
    return `<section class="page-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${s(badge)}</span></div><div class="report-card-list">${items.map((item) => `<article class="report-card"><div class="section-header"><h3>${s(item.title)}</h3><span class="status-badge">${s(item.badge || "统筹")}</span></div><p>${s(item.text)}</p>${item.route ? `<button type="button" data-jump="${s(item.route)}">查看</button>` : ""}</article>`).join("")}</div></section>`;
  }

  function hero(label, title, summary, sideTitle, sideValue) {
    return `<section class="report-hero"><div><p class="eyebrow">${s(label)}</p><h2>${s(title)}</h2><p>${s(summary)}</p></div><div class="report-hero-side"><span>${s(sideTitle)}</span><strong>${s(sideValue)}</strong><small>老板统筹层</small></div></section>`;
  }

  const ExecutiveCockpitPage = {
    route: "executive-cockpit",
    title: "经营驾驶舱",
    render() {
      const active = tasks();
      const high = active.filter((item) => item.priority === "高");
      return `${hero("EXECUTIVE COCKPIT", "经营驾驶舱", "老板只看经营结果、风险聚合、预算承接和组织闭环，不进入一线操作台。", "高风险", high.length)}${metricGrid([["待闭环任务", active.length, "跨模块汇总"], ["高优先级", high.length, "需要管理动作"], ["待复核", active.filter((item) => item.status === "待复核").length, "总管处理"], ["今日日志", logs().length, "可追溯"]])}${cards("老板统筹入口", "大局", [{title: "风险中心", text: "聚合商品、流量、库存、售后和报表异常，只看对利润和责任链有影响的风险。", route: "risk-center", badge: "风险"}, {title: "任务指挥", text: "查看任务是否被派发、是否被处理、是否复核归档。", route: "task-command", badge: "指挥"}, {title: "利润预算", text: "判断预算是否打到亏损商品上，活动是否压低毛利。", route: "profit-budget", badge: "利润"}, {title: "组织效率", text: "看总管和运营是否形成闭环，识别反复返工和卡点。", route: "org-efficiency", badge: "组织"}])}`;
    },
    mount(ctx) { ctx.delegate("[data-jump]", "click", (_, node) => AppRouter.navigate(node.dataset.jump)); },
  };

  const RiskCenterPage = {
    route: "risk-center",
    title: "风险中心",
    render() {
      const active = tasks();
      const riskItems = active.map((item) => ({ title: item.productShort || item.title, text: `${item.priority || "中"}风险 · ${item.reason || item.task || "需要确认经营影响"}`, badge: item.riskDomain || item.sourceModule, route: "task-command" }));
      return `${hero("RISK CENTER", "风险中心", "老板看到的是跨模块风险聚合。商品、竞品、上新、流量只是证据来源，不是老板的日常操作入口。", "风险项", riskItems.length)}${metricGrid([["售后 / 商品", active.filter((item) => item.riskDomain === "售后").length, "影响承接"], ["流量预算", active.filter((item) => item.riskDomain === "流量").length, "影响投放"], ["库存承接", active.filter((item) => item.riskDomain === "库存").length, "影响履约"], ["报表异常", active.filter((item) => item.riskDomain === "报表").length, "影响判断"]])}${cards("当前需要老板关注的风险", "聚合", riskItems.length ? riskItems : [{title: "暂无聚合风险", text: "当前没有需要老板直接关注的经营风险。", badge: "正常"}])}`;
    },
    mount(ctx) { ctx.delegate("[data-jump]", "click", (_, node) => AppRouter.navigate(node.dataset.jump)); },
  };

  const TaskCommandPage = {
    route: "task-command",
    title: "任务指挥",
    render() {
      const active = tasks();
      return `${hero("TASK COMMAND", "任务指挥", "老板在这里看任务是否被派发、处理、提交、复核和归档。具体执行仍交给总管和运营。", "待闭环", active.length)}${metricGrid([["未派发", active.filter((item) => !item.assigneeId).length, "需要下发"], ["处理中", active.filter((item) => item.status === "处理中").length, "运营执行"], ["待复核", active.filter((item) => item.status === "待复核").length, "总管复核"], ["高优先级", active.filter((item) => item.priority === "高").length, "优先看"]])}${cards("指挥队列", "任务", active.length ? active.map((item) => ({ title: item.title || item.productTitle, text: `${item.status || "待确认"} · ${item.assigneeName || "未派发"} · ${item.reason || item.task}`, badge: item.priority || "中", route: "business-actions" })) : [{title: "暂无任务", text: "当前没有需要指挥的任务。", badge: "空"}])}`;
    },
    mount(ctx) { ctx.delegate("[data-jump]", "click", (_, node) => AppRouter.navigate(node.dataset.jump)); },
  };

  const ProfitBudgetPage = {
    route: "profit-budget",
    title: "利润预算",
    render() {
      const active = tasks();
      const budgetRisks = active.filter((item) => ["流量", "价格", "售后"].includes(item.riskDomain));
      return `${hero("PROFIT & BUDGET", "利润预算", "把流量消耗、退款成本、库存资金和毛利承接放在一起看，避免预算继续放大亏损。", "预算风险", budgetRisks.length)}${metricGrid([["预算风险", budgetRisks.length, "ROI / 退款 / 毛利"], ["高优先级", budgetRisks.filter((item) => item.priority === "高").length, "先暂停放大"], ["流量相关", active.filter((item) => item.sourceRoute === "business-traffic").length, "投放承接"], ["财务可见", "是", "财务账号可看"]])}${cards("预算判断", "利润", budgetRisks.length ? budgetRisks.map((item) => ({ title: item.productShort || item.title, text: item.reason || "需要确认 ROI 是否真实、退款是否吞掉利润、库存是否能承接。", badge: item.priority || "中" })) : [{title: "暂无预算风险", text: "当前没有聚合出的预算风险。", badge: "正常"}])}`;
    },
  };

  const OrgEfficiencyPage = {
    route: "org-efficiency",
    title: "组织效率",
    render() {
      const active = tasks();
      const assigned = active.filter((item) => item.assigneeId);
      return `${hero("ORG EFFICIENCY", "组织效率", "老板看的是组织是否能闭环，不看一线操作细节。这里聚合派发、提交、复核和返工。", "已派发", assigned.length)}${metricGrid([["已派发", assigned.length, "责任已落位"], ["未派发", active.filter((item) => !item.assigneeId).length, "需要总管拆分"], ["待复核", active.filter((item) => item.status === "待复核").length, "管理卡点"], ["退回中", active.filter((item) => item.workflowStatus === "已退回").length, "质量问题"]])}${cards("组织卡点", "效率", [{title: "派发卡点", text: "未派发任务说明管理动作还没有落到具体运营。", badge: "派发"}, {title: "复核卡点", text: "待复核任务过多说明总管复核链路可能成为瓶颈。", badge: "复核"}, {title: "返工卡点", text: "退回任务说明执行证据不足或任务理解偏差。", badge: "返工"}])}`;
    },
  };

  const ReviewAuditPage = {
    route: "review-audit",
    title: "复核审计",
    render() {
      const logItems = logs().slice(0, 8).map((item) => ({ title: item.type || item.title, text: `${item.status || "已记录"} · ${item.action || item.result || "已进入日志"}`, badge: item.source || "日志" }));
      return `${hero("REVIEW AUDIT", "复核审计", "保留任务派发、提交、复核和归档痕迹，用来回看责任链和经营判断。", "日志", logs().length)}${metricGrid([["日志记录", logs().length, "可追溯"], ["任务归档", logs().filter((item) => String(item.status).includes("完成") || String(item.status).includes("归档")).length, "闭环"], ["派发记录", logs().filter((item) => String(item.type).includes("派发")).length, "责任链"], ["复核记录", logs().filter((item) => String(item.type).includes("复核")).length, "管理审计"]])}${cards("审计记录", "最近", logItems.length ? logItems : [{title: "暂无审计记录", text: "任务流转后会在这里形成可回看的记录。", badge: "空"}])}`;
    },
  };

  window.ExecutiveCockpitPage = ExecutiveCockpitPage;
  window.RiskCenterPage = RiskCenterPage;
  window.TaskCommandPage = TaskCommandPage;
  window.ProfitBudgetPage = ProfitBudgetPage;
  window.OrgEfficiencyPage = OrgEfficiencyPage;
  window.ReviewAuditPage = ReviewAuditPage;
})();
