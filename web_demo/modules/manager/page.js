(function () {
  const s = (value) => AppShell.escape(value);
  const managerTasks = [
    { source: "老板复盘审计", title: "抖音低 ROAS 商品预算收缩", owner: "店群总管", assignee: "待派发", status: "待拆分", priority: "高", due: "下周", review: "未提交", recap: "进入周报" },
    { source: "系统预警", title: "拼多多退款率商品专项复查", owner: "店群总管", assignee: "运营 B", status: "处理中", priority: "中", due: "今天 18:00", review: "未提交", recap: "进入日报" },
    { source: "经营模块", title: "厨房置物架售后优先处理", owner: "店群总管", assignee: "运营 A", status: "待复核", priority: "高", due: "今天 20:00", review: "待复核", recap: "进入日报" },
    { source: "月报草案", title: "库存资金占用降至 380,000 以下", owner: "数据财务", assignee: "待派发", status: "待确认", priority: "高", due: "下月", review: "未开始", recap: "进入月报" },
  ];
  const operators = [
    { name: "运营 A", load: 64, current: 2, done: 4, focus: "投流商品复查", state: "处理中" },
    { name: "运营 B", load: 28, current: 0, done: 2, focus: "售后差评处理", state: "可承接" },
    { name: "数据财务", load: 45, current: 1, done: 3, focus: "ROI / 库存复核", state: "在线" },
  ];
  const moduleSignals = [
    { module: "商品", abnormal: 3, task: 2, owner: "运营 B", next: "复查退货商品" },
    { module: "竞品", abnormal: 1, task: 0, owner: "运营 A", next: "观察竞品降价" },
    { module: "上新", abnormal: 2, task: 1, owner: "运营 A", next: "补齐素材尺寸" },
    { module: "流量", abnormal: 4, task: 2, owner: "运营 A", next: "收缩低 ROAS 预算" },
    { module: "售后", abnormal: 3, task: 2, owner: "运营 B", next: "压退款率" },
    { module: "库存", abnormal: 2, task: 1, owner: "数据财务", next: "清理滞销库存" },
  ];
  const recaps = [
    { type: "日报", status: "待提交", owner: "店群总管", focus: "退款率上升、低效投流、今日任务闭环" },
    { type: "周报", status: "草稿中", owner: "店群总管", focus: "周目标达成率、任务完成率、下周任务建议" },
    { type: "月报", status: "待补财务", owner: "数据财务", focus: "净利率、库存资金、广告费占比" },
    { type: "专项复盘", status: "待整理", owner: "运营 A", focus: "抖音小店低 ROAS 商品" },
  ];

  function activeTasks() { return window.AppTaskStore?.listActiveTasks?.() || []; }
  function hero(code, title, summary, label, value) { return `<section class="manager-hero"><div><p class="eyebrow">${s(code)}</p><h2>${s(title)}</h2><p>${s(summary)}</p></div><div class="manager-hero-side"><span>${s(label)}</span><strong>${s(value)}</strong><small>店群总管层</small></div></section>`; }
  function metricGrid(items) { return `<section class="kpi-grid manager-metrics">${items.map(([a, b, c]) => AppShell.metricCard(a, b, c)).join("")}</section>`; }
  function statusClass(value) { return ["已派发", "处理中", "在线", "可承接"].includes(value) ? "good" : ["待复核", "草稿中", "待补财务"].includes(value) ? "watch" : "warning"; }
  function taskCards(list = managerTasks) {
    return `<div class="manager-task-list">${list.map((item) => `<article class="manager-task-card"><div class="manager-task-top"><span class="status-dot ${statusClass(item.status)}"></span><strong>${s(item.title)}</strong><b>${s(item.priority)}</b></div><div class="manager-task-meta"><span>来源：${s(item.source)}</span><span>负责人：${s(item.assignee)}</span><span>截止：${s(item.due)}</span><span>复核：${s(item.review)}</span><span>${s(item.recap)}</span></div><p>状态：${s(item.status)} · 责任主管：${s(item.owner)}</p></article>`).join("")}</div>`;
  }
  function operatorCards() {
    return `<div class="manager-grid">${operators.map((item) => `<article class="manager-card"><div class="manager-card-head"><strong>${s(item.name)}</strong><span>${s(item.state)}</span></div><p>${s(item.focus)}</p><div class="manager-progress"><span style="width:${Math.min(100, item.load)}%"></span></div><small>当前 ${item.current} · 今日完成 ${item.done} · 负荷 ${item.load}%</small></article>`).join("")}</div>`;
  }
  function moduleCards() {
    return `<div class="manager-grid">${moduleSignals.map((item) => `<article class="manager-card"><div class="manager-card-head"><strong>${s(item.module)}</strong><span>异常 ${item.abnormal}</span></div><p>任务 ${item.task} · 负责人 ${s(item.owner)}</p><small>${s(item.next)}</small></article>`).join("")}</div>`;
  }
  function recapCards() {
    return `<div class="manager-grid">${recaps.map((item) => `<article class="manager-card"><div class="manager-card-head"><strong>${s(item.type)}</strong><span>${s(item.status)}</span></div><p>${s(item.focus)}</p><small>提交人：${s(item.owner)} · 提交后进入老板复盘审计</small></article>`).join("")}</div>`;
  }
  function table(title, head, rows) {
    return `<section class="page-section manager-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">MANAGER</span></div><div class="manager-table"><div class="manager-table-row head">${head.map((x) => `<span>${s(x)}</span>`).join("")}</div>${rows.map((row) => `<div class="manager-table-row">${row.map((x, i) => i ? `<span>${s(x)}</span>` : `<strong>${s(x)}</strong>`).join("")}</div>`).join("")}</div></section>`;
  }

  window.ManagerTasksPage = { route: "manager-tasks", title: "店群任务", render() { return `${hero("STORE GROUP TASKS", "店群任务", "承接老板复盘审计任务、系统预警任务和经营模块任务，先确认来源、周期、责任人和是否进入复盘。", "任务池", managerTasks.length)}${metricGrid([["老板下发", 1, "复盘审计来源"], ["系统预警", 1, "经营异常来源"], ["待拆分", managerTasks.filter(x => x.status === "待拆分").length, "需要总管拆解"], ["待复核", managerTasks.filter(x => x.status === "待复核").length, "运营已提交"]])}<section class="page-section manager-section"><div class="section-header"><h3>店群任务池</h3><button type="button" data-go="manager-dispatch">进入任务派发</button></div>${taskCards()}</section>`; }, mount(ctx) { ctx.delegate("[data-go]", "click", (_, node) => AppRouter.navigate(node.dataset.go)); } };

  window.ManagerDispatchPage = { route: "manager-dispatch", title: "任务派发", render() { return `${hero("TASK DISPATCH", "任务派发", "总管把老板任务、系统任务拆给运营，并设置负责人、截止时间、复核标准和复盘归档口径。", "待派发", managerTasks.filter(x => x.assignee === "待派发").length)}${metricGrid([["待派发", managerTasks.filter(x => x.assignee === "待派发").length, "需要指定运营"], ["已派发", managerTasks.filter(x => x.assignee !== "待派发").length, "责任已落位"], ["可承接", operators.filter(x => x.state === "可承接").length, "运营空闲"], ["高优先级", managerTasks.filter(x => x.priority === "高").length, "优先拆分"]])}<section class="page-section manager-section"><div class="section-header"><h3>运营负荷</h3><span class="status-badge">LOAD</span></div>${operatorCards()}</section><section class="page-section manager-section"><div class="section-header"><h3>待派发任务</h3><span class="status-badge">DISPATCH</span></div>${taskCards(managerTasks.filter(x => x.assignee === "待派发"))}</section>`; } };

  window.ManagerReviewPage = { route: "manager-review", title: "运营复核", render() { const review = managerTasks.filter(x => x.review === "待复核"); return `${hero("OPERATION REVIEW", "运营复核", "总管复核运营提交结果，判断是否通过、退回补充，或进入日报 / 周报复盘。", "待复核", review.length)}${metricGrid([["待复核", review.length, "需要总管确认"], ["已退回", 1, "需补充证据"], ["今日完成", 4, "团队产出"], ["需写复盘", managerTasks.filter(x => x.recap.includes("进入")).length, "沉淀报告"]])}<section class="page-section manager-section"><div class="section-header"><h3>复核队列</h3><span class="status-badge">REVIEW</span></div>${taskCards(review.length ? review : managerTasks.slice(0, 2))}</section>`; } };

  window.ManagerModulesPage = { route: "manager-modules", title: "经营模块", render() { return `${hero("OPERATION MODULES", "经营模块", "商品、竞品、上新、流量、售后、库存不再平铺在左侧，而是在这里作为总管查原因和拆任务的入口。", "模块", moduleSignals.length)}${metricGrid([["异常模块", moduleSignals.filter(x => x.abnormal > 0).length, "需要关注"], ["模块任务", moduleSignals.reduce((n,x)=>n+x.task,0), "已进入任务池"], ["最高异常", "流量", "ROAS 低"], ["售后关注", "退款率", "拼多多偏高"]])}<section class="page-section manager-section"><div class="section-header"><h3>经营模块入口</h3><span class="status-badge">MODULES</span></div>${moduleCards()}</section>`; } };

  window.ManagerRetrospectivePage = { route: "manager-retrospective", title: "复盘提交", render() { return `${hero("RETROSPECTIVE SUBMIT", "复盘提交", "总管提交日报、周报、月报和专项复盘，老板在复盘审计中接收并定下周期任务。", "待提交", recaps.filter(x => x.status.includes("待")).length)}${metricGrid([["日报", "待提交", "今日经营"], ["周报", "草稿中", "目标达成"], ["月报", "待补财务", "利润库存"], ["专项复盘", "待整理", "投流问题"]])}<section class="page-section manager-section"><div class="section-header"><h3>复盘提交队列</h3><span class="status-badge">SUBMIT</span></div>${recapCards()}</section>`; } };

  window.ManagerReportsPage = { route: "manager-reports", title: "数据报表", render() { return `${hero("DATA REPORTS", "数据报表", "数据报表服务于总管写复盘：订单、投流、售后、库存和任务闭环都要能作为日报 / 周报依据。", "报表", 5)}${metricGrid([["订单报表", "已同步", "店铺销售"], ["投流报表", "关注", "ROAS 低"], ["售后报表", "关注", "退款率"], ["库存报表", "待复核", "资金占用"]])}${table("复盘数据依据", ["报表", "状态", "用途", "下一步"], [["订单报表", "已同步", "日报 / 周报销售达成", "写入周报"], ["投流报表", "关注", "ROAS 和消耗判断", "生成专项复盘"], ["售后报表", "关注", "退款和差评判断", "进入日报"], ["库存报表", "待复核", "库存资金占用", "进入月报"]])}`; } };
})();
