(function () {
  const s = (value) => AppShell.escape(value);

  const STORE_OVERVIEW = [
    { id: "S001", platform: "淘宝", name: "家居生活主店", products: 126, activeProducts: 84, todayOrders: 236, orderTrend: "+8.4%", sales: 42800, salesTrend: "+12.1%", profit: 9100, profitTrend: "+4.6%", comments: 18320, badComments: 42, refundRate: "3.2%", stockAmount: 186000, pendingTasks: 1, syncDelay: 3, syncStatus: "正常", status: "稳定" },
    { id: "S002", platform: "拼多多", name: "家居百货店", products: 98, activeProducts: 67, todayOrders: 318, orderTrend: "+11.6%", sales: 35600, salesTrend: "+9.2%", profit: 6200, profitTrend: "-2.1%", comments: 24680, badComments: 76, refundRate: "5.8%", stockAmount: 142000, pendingTasks: 1, syncDelay: 7, syncStatus: "关注", status: "关注" },
    { id: "S003", platform: "抖音小店", name: "家居好物号", products: 64, activeProducts: 39, todayOrders: 152, orderTrend: "+5.1%", sales: 29800, salesTrend: "+7.7%", profit: 4800, profitTrend: "-3.8%", comments: 10560, badComments: 33, refundRate: "6.1%", stockAmount: 98000, pendingTasks: 1, syncDelay: 12, syncStatus: "延迟", status: "关注" },
  ];

  function tasks() { return window.AppTaskStore?.listActiveTasks?.() || []; }
  function logs() { return window.AppTaskStore?.listLogs?.() || []; }
  function sum(key) { return STORE_OVERVIEW.reduce((total, item) => total + Number(item[key] || 0), 0); }
  function money(value) { return `¥${Number(value || 0).toLocaleString("zh-CN")}`; }
  function trendClass(value) { return String(value || "").startsWith("-") ? "down" : "up"; }
  function syncClass(value) { return value === "正常" ? "good" : value === "延迟" ? "warning" : "watch"; }
  function currentTime() { return new Date().toLocaleTimeString("zh-CN", { hour12: false }); }
  function metricGrid(items) { return `<section class="kpi-grid report-metrics realtime-metrics">${items.map(([a, b, c, t]) => `<article class="card realtime-metric"><h3>${s(a)}</h3><strong>${s(b)}</strong><small>${s(c)}</small>${t ? `<em class="trend ${trendClass(t)}">${s(t)}</em>` : ""}</article>`).join("")}</section>`; }
  function hero(label, title, summary, sideTitle, sideValue) { return `<section class="report-hero realtime-hero"><div><p class="eyebrow">${s(label)}</p><h2>${s(title)}</h2><p>${s(summary)}</p></div><div class="report-hero-side"><span>${s(sideTitle)}</span><strong>${s(sideValue)}</strong><small>实时经营盘面</small></div></section>`; }

  function realtimeBar() {
    const delayed = STORE_OVERVIEW.filter((item) => item.syncStatus === "延迟").length;
    return `<section class="realtime-strip"><div><span class="pulse-dot"></span><strong>实时同步中</strong><small>ERP ${s(currentTime())}</small></div><div><span class="status-dot good"></span>淘宝已同步</div><div><span class="status-dot good"></span>拼多多已同步</div><div><span class="status-dot ${delayed ? "warning" : "good"}"></span>抖音小店${delayed ? "延迟 12 秒" : "已同步"}</div><div>任务池 ${tasks().length} 条待处理</div></section>`;
  }

  function platformCards() {
    const platforms = Array.from(new Set(STORE_OVERVIEW.map((item) => item.platform)));
    return `<section class="page-section realtime-section"><div class="section-header"><h3>平台实时经营</h3><span class="status-badge">LIVE</span></div><div class="platform-grid">${platforms.map((platform) => {
      const stores = STORE_OVERVIEW.filter((item) => item.platform === platform);
      const products = stores.reduce((total, item) => total + item.products, 0);
      const orders = stores.reduce((total, item) => total + item.todayOrders, 0);
      const sales = stores.reduce((total, item) => total + item.sales, 0);
      const profit = stores.reduce((total, item) => total + item.profit, 0);
      const comments = stores.reduce((total, item) => total + item.comments, 0);
      const pending = stores.reduce((total, item) => total + item.pendingTasks, 0);
      const status = stores.some((item) => item.syncStatus === "延迟") ? "延迟" : stores.some((item) => item.status === "关注") ? "关注" : "正常";
      return `<article class="platform-card"><div class="platform-head"><div><span class="status-dot ${syncClass(status)}"></span><strong>${s(platform)}</strong></div><span>${stores.length} 店 · ${s(status)}</span></div><div class="platform-numbers"><div><small>订单</small><b>${orders}</b></div><div><small>销售额</small><b>${s(money(sales))}</b></div><div><small>利润</small><b>${s(money(profit))}</b></div><div><small>评论</small><b>${comments.toLocaleString("zh-CN")}</b></div></div><div class="platform-progress"><span style="width:${Math.min(100, Math.round((orders / Math.max(orders + 120, 1)) * 100))}%"></span></div><footer>商品 ${products} · 待办 ${pending} · ${s(currentTime())}</footer></article>`;
    }).join("")}</div></section>`;
  }

  function storeTable() {
    const rows = STORE_OVERVIEW.map((store) => `<div class="store-table-row"><strong>${s(store.name)}</strong><span><i class="status-dot ${syncClass(store.syncStatus)}"></i>${s(store.platform)}</span><span>${store.products}</span><span>${store.activeProducts}</span><span>${store.todayOrders}<em class="trend ${trendClass(store.orderTrend)}">${s(store.orderTrend)}</em></span><span>${s(money(store.sales))}<em class="trend ${trendClass(store.salesTrend)}">${s(store.salesTrend)}</em></span><span>${s(money(store.profit))}<em class="trend ${trendClass(store.profitTrend)}">${s(store.profitTrend)}</em></span><span>${store.comments.toLocaleString("zh-CN")}</span><span>${store.badComments}</span><span>${s(store.refundRate)}</span><span>${s(money(store.stockAmount))}</span><span>${store.pendingTasks}</span><span><b class="state-pill ${store.status === "稳定" ? "good" : "warning"}">${s(store.status)}</b></span></div>`).join("");
    return `<section class="page-section realtime-section"><div class="section-header"><h3>店铺经营明细</h3><span class="status-badge">TABLE</span></div><div class="store-table"><div class="store-table-row head"><span>店铺</span><span>平台</span><span>商品</span><span>动销</span><span>订单</span><span>销售额</span><span>利润</span><span>评论</span><span>差评</span><span>退款率</span><span>库存金额</span><span>待办</span><span>状态</span></div>${rows}</div></section>`;
  }

  const StoreOverviewPage = {
    route: "store-overview",
    title: "店群总览",
    render() {
      const active = tasks();
      const avgRefund = "5.0%";
      return `${hero("STORE GROUP LIVE BOARD", "店群总览", "老板先看实时经营盘面：平台、店铺、商品、订单、销售额、利润、评论、退款、库存和待办。异常只作为字段状态，不抢第一屏结论。", "运营店铺", STORE_OVERVIEW.length)}${realtimeBar()}${metricGrid([["运营平台", new Set(STORE_OVERVIEW.map((item) => item.platform)).size, "淘宝 / 拼多多 / 抖音"], ["店铺数量", STORE_OVERVIEW.length, "当前运营中"], ["在线商品", sum("products"), "全部店铺"], ["今日订单", sum("todayOrders"), "实时经营", "+8.9%"], ["今日销售额", money(sum("sales")), "跨平台汇总", "+10.4%"], ["今日利润", money(sum("profit")), "预估毛利", "-0.8%"], ["退款率", avgRefund, "跨店均值", "+0.7%"], ["库存金额", money(sum("stockAmount")), "资金占用"]])}${platformCards()}${storeTable()}`;
    },
  };

  const TaskCommandPage = {
    route: "task-command",
    title: "任务指挥",
    render() {
      const active = tasks();
      return `${hero("TASK COMMAND", "任务指挥", "老板在这里看任务是否被派发、处理、提交、复核和归档。具体执行仍交给总管和运营。", "待闭环", active.length)}${metricGrid([["未派发", active.filter((item) => !item.assigneeId).length, "需要下发"], ["处理中", active.filter((item) => item.status === "处理中").length, "运营执行"], ["待复核", active.filter((item) => item.status === "待复核").length, "总管复核"], ["高优先级", active.filter((item) => item.priority === "高").length, "优先看"]])}`;
    },
  };

  const ProfitBudgetPage = {
    route: "profit-budget",
    title: "利润预算",
    render() {
      const active = tasks();
      const budgetRisks = active.filter((item) => ["流量", "价格", "售后"].includes(item.riskDomain));
      return `${hero("PROFIT & BUDGET", "利润预算", "把流量消耗、退款成本、库存资金和毛利承接放在一起看，避免预算继续放大亏损。", "预算关注", budgetRisks.length)}${metricGrid([["销售额", money(sum("sales")), "今日汇总"], ["利润", money(sum("profit")), "预估毛利"], ["库存资金", money(sum("stockAmount")), "资金占用"], ["预算关注", budgetRisks.length, "ROI / 退款 / 毛利"]])}`;
    },
  };

  const OrgEfficiencyPage = {
    route: "org-efficiency",
    title: "组织效率",
    render() {
      const active = tasks();
      const assigned = active.filter((item) => item.assigneeId);
      return `${hero("ORG EFFICIENCY", "组织效率", "老板看的是组织是否能闭环，不看一线操作细节。这里聚合派发、提交、复核和返工。", "已派发", assigned.length)}${metricGrid([["已派发", assigned.length, "责任已落位"], ["未派发", active.filter((item) => !item.assigneeId).length, "需要总管拆分"], ["待复核", active.filter((item) => item.status === "待复核").length, "管理卡点"], ["退回中", active.filter((item) => item.workflowStatus === "已退回").length, "质量问题"]])}`;
    },
  };

  const ReviewAuditPage = {
    route: "review-audit",
    title: "复核审计",
    render() {
      const logItems = logs().slice(0, 8).map((item) => ({ title: item.type || item.title, text: `${item.status || "已记录"} · ${item.action || item.result || "已进入日志"}`, badge: item.source || "日志" }));
      return `${hero("REVIEW AUDIT", "复核审计", "保留任务派发、提交、复核和归档痕迹，用来回看责任链和经营判断。", "日志", logs().length)}${metricGrid([["日志记录", logs().length, "可追溯"], ["任务归档", logs().filter((item) => String(item.status).includes("完成") || String(item.status).includes("归档")).length, "闭环"], ["派发记录", logs().filter((item) => String(item.type).includes("派发")).length, "责任链"], ["复核记录", logs().filter((item) => String(item.type).includes("复核")).length, "管理审计"]])}`;
    },
  };

  window.StoreOverviewPage = StoreOverviewPage;
  window.TaskCommandPage = TaskCommandPage;
  window.ProfitBudgetPage = ProfitBudgetPage;
  window.OrgEfficiencyPage = OrgEfficiencyPage;
  window.ReviewAuditPage = ReviewAuditPage;
})();
