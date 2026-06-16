(function () {
  const s = (value) => AppShell.escape(value);

  const STORE_OVERVIEW = [
    { id: "S001", platform: "淘宝", name: "家居生活主店", products: 126, activeProducts: 84, todayOrders: 236, sales: 42800, profit: 9100, comments: 18320, badComments: 42, refundRate: "3.2%", stockAmount: 186000, pendingTasks: 1, status: "关注" },
    { id: "S002", platform: "拼多多", name: "家居百货店", products: 98, activeProducts: 67, todayOrders: 318, sales: 35600, profit: 6200, comments: 24680, badComments: 76, refundRate: "5.8%", stockAmount: 142000, pendingTasks: 1, status: "关注" },
    { id: "S003", platform: "抖音小店", name: "家居好物号", products: 64, activeProducts: 39, todayOrders: 152, sales: 29800, profit: 4800, comments: 10560, badComments: 33, refundRate: "6.1%", stockAmount: 98000, pendingTasks: 1, status: "关注" },
  ];

  function tasks() { return window.AppTaskStore?.listActiveTasks?.() || []; }
  function logs() { return window.AppTaskStore?.listLogs?.() || []; }
  function sum(key) { return STORE_OVERVIEW.reduce((total, item) => total + Number(item[key] || 0), 0); }
  function money(value) { return `¥${Number(value || 0).toLocaleString("zh-CN")}`; }
  function metricGrid(items) { return `<section class="kpi-grid report-metrics">${items.map(([a, b, c]) => AppShell.metricCard(a, b, c)).join("")}</section>`; }
  function cards(title, badge, items) { return `<section class="page-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${s(badge)}</span></div><div class="report-card-list">${items.map((item) => `<article class="report-card"><div class="section-header"><h3>${s(item.title)}</h3><span class="status-badge">${s(item.badge || "统筹")}</span></div><p>${s(item.text)}</p>${item.route ? `<button type="button" data-jump="${s(item.route)}">查看</button>` : ""}</article>`).join("")}</div></section>`; }
  function hero(label, title, summary, sideTitle, sideValue) { return `<section class="report-hero"><div><p class="eyebrow">${s(label)}</p><h2>${s(title)}</h2><p>${s(summary)}</p></div><div class="report-hero-side"><span>${s(sideTitle)}</span><strong>${s(sideValue)}</strong><small>老板统筹层</small></div></section>`; }

  function platformSummary() {
    const platforms = Array.from(new Set(STORE_OVERVIEW.map((item) => item.platform)));
    return platforms.map((platform) => {
      const stores = STORE_OVERVIEW.filter((item) => item.platform === platform);
      const products = stores.reduce((total, item) => total + item.products, 0);
      const orders = stores.reduce((total, item) => total + item.todayOrders, 0);
      const sales = stores.reduce((total, item) => total + item.sales, 0);
      const profit = stores.reduce((total, item) => total + item.profit, 0);
      const comments = stores.reduce((total, item) => total + item.comments, 0);
      const tasks = stores.reduce((total, item) => total + item.pendingTasks, 0);
      return { title: platform, badge: `${stores.length} 店`, text: `商品 ${products} · 今日订单 ${orders} · 销售额 ${money(sales)} · 利润 ${money(profit)} · 评论 ${comments.toLocaleString("zh-CN")} · 待办 ${tasks}` };
    });
  }

  function storeRows() {
    return STORE_OVERVIEW.map((store) => ({
      title: store.name,
      badge: store.platform,
      text: `${store.status} · 商品 ${store.products} · 动销 ${store.activeProducts} · 今日订单 ${store.todayOrders} · 销售额 ${money(store.sales)} · 利润 ${money(store.profit)} · 评论 ${store.comments.toLocaleString("zh-CN")} · 差评 ${store.badComments} · 退款率 ${store.refundRate} · 库存金额 ${money(store.stockAmount)} · 待办 ${store.pendingTasks}`,
    }));
  }

  const StoreOverviewPage = {
    route: "store-overview",
    title: "店群总览",
    render() {
      const active = tasks();
      return `${hero("STORE GROUP OVERVIEW", "店群总览", "老板先看平台、店铺、商品、订单、销售额、利润、评论、退款、库存和待办数量。风险不是第一屏结论，而是从盘面数据里钻取出来。", "运营店铺", STORE_OVERVIEW.length)}${metricGrid([["运营平台", new Set(STORE_OVERVIEW.map((item) => item.platform)).size, "淘宝 / 拼多多 / 抖音"], ["店铺数量", STORE_OVERVIEW.length, "当前运营中"], ["在线商品", sum("products"), "全部店铺"], ["今日订单", sum("todayOrders"), "实时经营"], ["今日销售额", money(sum("sales")), "跨平台汇总"], ["今日利润", money(sum("profit")), "预估毛利"], ["评论总数", sum("comments").toLocaleString("zh-CN"), "口碑资产"], ["待处理任务", active.length, "进入指挥"]])}${cards("平台汇总", "平台", platformSummary())}${cards("店铺经营明细", "店铺", storeRows())}`;
    },
  };

  const TaskCommandPage = {
    route: "task-command",
    title: "任务指挥",
    render() {
      const active = tasks();
      return `${hero("TASK COMMAND", "任务指挥", "老板在这里看任务是否被派发、处理、提交、复核和归档。具体执行仍交给总管和运营。", "待闭环", active.length)}${metricGrid([["未派发", active.filter((item) => !item.assigneeId).length, "需要下发"], ["处理中", active.filter((item) => item.status === "处理中").length, "运营执行"], ["待复核", active.filter((item) => item.status === "待复核").length, "总管复核"], ["高优先级", active.filter((item) => item.priority === "高").length, "优先看"]])}${cards("指挥队列", "任务", active.length ? active.map((item) => ({ title: item.title || item.productTitle, text: `${item.status || "待确认"} · ${item.assigneeName || "未派发"} · ${item.reason || item.task}`, badge: item.priority || "中" })) : [{title: "暂无任务", text: "当前没有需要指挥的任务。", badge: "空"}])}`;
    },
  };

  const ProfitBudgetPage = {
    route: "profit-budget",
    title: "利润预算",
    render() {
      const active = tasks();
      const budgetRisks = active.filter((item) => ["流量", "价格", "售后"].includes(item.riskDomain));
      return `${hero("PROFIT & BUDGET", "利润预算", "把流量消耗、退款成本、库存资金和毛利承接放在一起看，避免预算继续放大亏损。", "预算关注", budgetRisks.length)}${metricGrid([["销售额", money(sum("sales")), "今日汇总"], ["利润", money(sum("profit")), "预估毛利"], ["库存资金", money(sum("stockAmount")), "资金占用"], ["预算关注", budgetRisks.length, "ROI / 退款 / 毛利"]])}${cards("预算判断", "利润", budgetRisks.length ? budgetRisks.map((item) => ({ title: item.productShort || item.title, text: item.reason || "需要确认 ROI 是否真实、退款是否吞掉利润、库存是否能承接。", badge: item.priority || "中" })) : [{title: "暂无预算关注项", text: "当前没有聚合出的预算关注项。", badge: "正常"}])}`;
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

  window.StoreOverviewPage = StoreOverviewPage;
  window.TaskCommandPage = TaskCommandPage;
  window.ProfitBudgetPage = ProfitBudgetPage;
  window.OrgEfficiencyPage = OrgEfficiencyPage;
  window.ReviewAuditPage = ReviewAuditPage;
})();
