(function () {
  const s = (value) => AppShell.escape(value);
  const STATE_KEY = "manager_task_state_v239";
  const SORT_KEY = "manager_task_sort_v239";
  const SELECTED_KEY = "manager_selected_task_v239";

  const baseTasks = [
    { id: "MT-001", source: "老板复盘审计", sourceRank: 1, title: "抖音低 ROAS 商品预算收缩", owner: "店群总管", assignee: "待派发", status: "待拆分", priority: "高", priorityRank: 1, due: "下周", dueRank: 70, review: "未提交", recap: "进入周报", sourceReport: "本周周报 + 抖音专项复盘", impact: "抖音小店 / 低 ROAS 商品", goal: "降低低效投流消耗，提高下周 ROAS。", detail: "老板从复盘审计中确认抖音低 ROAS 不是单日波动，需要总管拆成运营可执行动作。", evidence: ["抖音 ROAS 1.8，低于目标 2.5。", "低效投流持续 3 天。", "广告费占比上升，净利率被压低。"], agentChecks: ["检索近 7 天广告消耗与订单利润。", "识别低 ROAS 商品清单。", "判断停投、降预算或换素材建议。"], split: ["运营 A：筛出低 ROAS 商品清单。", "数据财务：复核广告消耗、利润和 ROI。", "店群总管：确认停投 / 降预算比例。"] },
    { id: "MT-002", source: "系统预警", sourceRank: 2, title: "拼多多退款率商品专项复查", owner: "店群总管", assignee: "运营 B", status: "处理中", priority: "中", priorityRank: 2, due: "今天 18:00", dueRank: 10, review: "未提交", recap: "进入日报", sourceReport: "售后预警", impact: "拼多多 / 家居百货店", goal: "压低退款率，减少售后吞利。", detail: "退款率上升已经影响日利润，需要运营补齐差评和退货原因。", evidence: ["拼多多退款率 5.8%。", "差评集中在安装、尺寸咨询和售后响应。"], agentChecks: ["检索退款订单原因。", "检查差评商品是否已进入处理任务。", "判断是否需要修改商品页和客服话术。"], split: ["运营 B：整理退款原因和差评商品。", "店群总管：复核商品页、客服话术和物流问题。"] },
    { id: "MT-003", source: "经营模块", sourceRank: 3, title: "厨房置物架售后优先处理", owner: "店群总管", assignee: "运营 A", status: "待复核", priority: "高", priorityRank: 1, due: "今天 20:00", dueRank: 12, review: "待复核", recap: "进入日报", sourceReport: "商品 / 售后模块", impact: "厨房置物架", goal: "确认售后动作是否有效，避免问题进入周报未达标项。", detail: "运营已提交初步处理，总管需要确认处理结果是否达标。", evidence: ["运营已补充售后处理说明。", "仍需确认差评商品是否下架或改文案。"], agentChecks: ["检索运营提交证据。", "判断处理后退款率是否下降。", "判断是否通过或退回补充。"], split: ["总管：复核运营提交。", "运营 A：必要时补充证据。"] },
    { id: "MT-004", source: "月报草案", sourceRank: 4, title: "库存资金占用降至 380,000 以下", owner: "数据财务", assignee: "待派发", status: "待确认", priority: "高", priorityRank: 1, due: "下月", dueRank: 90, review: "未开始", recap: "进入月报", sourceReport: "月报草案", impact: "供应链 / 库存资金", goal: "降低库存占用，释放现金流。", detail: "月报显示库存资金压力偏高，需要从供应商节奏和滞销库存清理切入。", evidence: ["当前库存资金 426,000。", "目标为 380,000 以下。", "部分供应商成本上浮。"], agentChecks: ["检索库存周转、滞销库存和补货记录。", "判断供应商补货节奏是否需要调整。", "生成月度库存压降拆分任务。"], split: ["数据财务：输出库存资金明细。", "店群总管：确认滞销清理策略。", "运营：配合商品页促销或下架。"] },
  ];

  const operators = [
    { name: "运营 A", load: 64, current: 2, done: 4, focus: "投流商品复查", state: "处理中" },
    { name: "运营 B", load: 28, current: 0, done: 2, focus: "售后差评处理", state: "可承接" },
    { name: "数据财务", load: 45, current: 1, done: 3, focus: "ROI / 库存复核", state: "在线" },
  ];
  const moduleSignals = [
    { module: "商品", abnormal: 3, task: 2, owner: "运营 B", next: "复查退货商品" }, { module: "竞品", abnormal: 1, task: 0, owner: "运营 A", next: "观察竞品降价" }, { module: "上新", abnormal: 2, task: 1, owner: "运营 A", next: "补齐素材尺寸" },
    { module: "流量", abnormal: 4, task: 2, owner: "运营 A", next: "收缩低 ROAS 预算" }, { module: "售后", abnormal: 3, task: 2, owner: "运营 B", next: "压退款率" }, { module: "库存", abnormal: 2, task: 1, owner: "数据财务", next: "清理滞销库存" },
  ];
  const recaps = [
    { type: "日报", status: "待提交", owner: "店群总管", focus: "退款率上升、低效投流、今日任务闭环" }, { type: "周报", status: "草稿中", owner: "店群总管", focus: "周目标达成率、任务完成率、下周任务建议" },
    { type: "月报", status: "待补财务", owner: "数据财务", focus: "净利率、库存资金、广告费占比" }, { type: "专项复盘", status: "待整理", owner: "运营 A", focus: "抖音小店低 ROAS 商品" },
  ];

  function state() { try { return JSON.parse(localStorage.getItem(STATE_KEY) || "{}"); } catch (_) { return {}; } }
  function saveState(next) { localStorage.setItem(STATE_KEY, JSON.stringify(next || {})); }
  function tasks() { const st = state(); return baseTasks.map((task) => ({ ...task, ...(st[task.id] || {}) })); }
  function currentSort() { return localStorage.getItem(SORT_KEY) || "time"; }
  function setSelected(id) { localStorage.setItem(SELECTED_KEY, id || "MT-001"); }
  function selectedTask(ctx) { const id = ctx?.state?.taskId || localStorage.getItem(SELECTED_KEY) || "MT-001"; return tasks().find((task) => task.id === id) || tasks()[0]; }
  function updateTask(id, patch) { const st = state(); st[id] = { ...(st[id] || {}), ...patch }; saveState(st); }
  function sortedTasks(list = tasks()) {
    const mode = currentSort();
    const statusRank = { "已逾期": 0, "待复核": 1, "待拆分": 2, "待确认": 3, "处理中": 4, "已派发": 5, "已归档": 6 };
    const compare = {
      time: (a, b) => a.dueRank - b.dueRank || a.priorityRank - b.priorityRank,
      priority: (a, b) => a.priorityRank - b.priorityRank || a.dueRank - b.dueRank,
      source: (a, b) => a.sourceRank - b.sourceRank || a.dueRank - b.dueRank,
      status: (a, b) => (statusRank[a.status] ?? 9) - (statusRank[b.status] ?? 9) || a.dueRank - b.dueRank,
    }[mode] || ((a, b) => a.dueRank - b.dueRank);
    return [...list].sort(compare);
  }
  function activeTasks() { return window.AppTaskStore?.listActiveTasks?.() || []; }
  function hero(code, title, summary, label, value) { return `<section class="manager-hero"><div><p class="eyebrow">${s(code)}</p><h2>${s(title)}</h2><p>${s(summary)}</p></div><div class="manager-hero-side"><span>${s(label)}</span><strong>${s(value)}</strong><small>店群总管层</small></div></section>`; }
  function metricGrid(items) { return `<section class="kpi-grid manager-metrics">${items.map(([a, b, c]) => AppShell.metricCard(a, b, c)).join("")}</section>`; }
  function statusClass(value) { return ["已派发", "处理中", "在线", "可承接", "已归档"].includes(value) ? "good" : ["待复核", "草稿中", "待补财务", "待确认"].includes(value) ? "watch" : "warning"; }
  function sortBar() { return `<div class="manager-sort-bar"><button data-sort="time" class="${currentSort() === "time" ? "active" : ""}">按时间</button><button data-sort="priority" class="${currentSort() === "priority" ? "active" : ""}">按优先级</button><button data-sort="source" class="${currentSort() === "source" ? "active" : ""}">按来源</button><button data-sort="status" class="${currentSort() === "status" ? "active" : ""}">按状态</button></div>`; }
  function actionRow(task) { return `<div class="manager-action-row"><button type="button" data-detail="${s(task.id)}">查看详情</button><button type="button" class="secondary" data-split="${s(task.id)}">拆分任务</button><button type="button" class="secondary" data-dispatch="${s(task.id)}">派发运营</button></div>`; }
  function taskCards(list = tasks()) {
    const rows = sortedTasks(list);
    return `<div class="manager-task-list">${rows.map((item) => `<article class="manager-task-card"><div class="manager-task-top"><span class="status-dot ${statusClass(item.status)}"></span><strong>${s(item.title)}</strong><b>${s(item.priority)}</b></div><div class="manager-task-meta"><span>来源：${s(item.source)}</span><span>负责人：${s(item.assignee)}</span><span>截止：${s(item.due)}</span><span>复核：${s(item.review)}</span><span>${s(item.recap)}</span></div><p>状态：${s(item.status)} · 责任主管：${s(item.owner)} · ${s(item.goal)}</p>${actionRow(item)}</article>`).join("")}</div>`;
  }
  function operatorCards() { return `<div class="manager-grid">${operators.map((item) => `<article class="manager-card"><div class="manager-card-head"><strong>${s(item.name)}</strong><span>${s(item.state)}</span></div><p>${s(item.focus)}</p><div class="manager-progress"><span style="width:${Math.min(100, item.load)}%"></span></div><small>当前 ${item.current} · 今日完成 ${item.done} · 负荷 ${item.load}%</small></article>`).join("")}</div>`; }
  function moduleCards() { return `<div class="manager-grid">${moduleSignals.map((item) => `<article class="manager-card"><div class="manager-card-head"><strong>${s(item.module)}</strong><span>异常 ${item.abnormal}</span></div><p>任务 ${item.task} · 负责人 ${s(item.owner)}</p><small>${s(item.next)}</small></article>`).join("")}</div>`; }
  function recapCards() { return `<div class="manager-grid">${recaps.map((item) => `<article class="manager-card"><div class="manager-card-head"><strong>${s(item.type)}</strong><span>${s(item.status)}</span></div><p>${s(item.focus)}</p><small>提交人：${s(item.owner)} · 提交后进入老板复盘审计</small></article>`).join("")}</div>`; }
  function detailBlock(title, rows) { return `<section class="manager-detail-block"><h3>${s(title)}</h3><ul>${rows.map((row) => `<li>${s(row)}</li>`).join("")}</ul></section>`; }
  function detailPage(task) {
    return `${hero("TASK DETAIL · AGENT READY", task.title, "任务详情页承接复盘、预警、经营模块来源，后续 Agent 会在这里检索证据并给出拆分 / 派发 / 复核判断。", "当前状态", task.status)}<section class="page-section manager-section"><div class="section-header"><h3>任务基础信息</h3><button type="button" data-go="manager-tasks">返回店群任务</button></div><div class="manager-detail-grid"><article><span>任务来源</span><strong>${s(task.source)}</strong></article><article><span>来源报告</span><strong>${s(task.sourceReport)}</strong></article><article><span>影响范围</span><strong>${s(task.impact)}</strong></article><article><span>责任人</span><strong>${s(task.assignee)}</strong></article><article><span>截止时间</span><strong>${s(task.due)}</strong></article><article><span>复盘口径</span><strong>${s(task.recap)}</strong></article></div><p class="manager-detail-note">${s(task.detail)}</p></section><section class="manager-detail-panels">${detailBlock("数据证据", task.evidence)}${detailBlock("Agent 判断预留", task.agentChecks)}${detailBlock("建议拆分动作", task.split)}</section><section class="page-section manager-section"><div class="section-header"><h3>动作流</h3><span class="status-badge">SPLIT · DISPATCH · REVIEW</span></div><div class="manager-action-row"><button type="button" data-split="${s(task.id)}">拆分任务</button><button type="button" data-dispatch="${s(task.id)}">派发给运营</button><button type="button" class="secondary" data-review="${s(task.id)}">进入复核</button><button type="button" class="secondary" data-recap="${s(task.id)}">写入复盘</button></div></section>`;
  }
  function table(title, head, rows) { return `<section class="page-section manager-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">MANAGER</span></div><div class="manager-table"><div class="manager-table-row head">${head.map((x) => `<span>${s(x)}</span>`).join("")}</div>${rows.map((row) => `<div class="manager-table-row">${row.map((x, i) => i ? `<span>${s(x)}</span>` : `<strong>${s(x)}</strong>`).join("")}</div>`).join("")}</div></section>`; }
  function managerMount(ctx) {
    ctx.delegate("[data-sort]", "click", (_, node) => { localStorage.setItem(SORT_KEY, node.dataset.sort); AppRouter.schedule("manager-sort"); });
    ctx.delegate("[data-detail]", "click", (_, node) => { setSelected(node.dataset.detail); AppRouter.navigate("manager-task-detail", { taskId: node.dataset.detail }); });
    ctx.delegate("[data-split]", "click", (_, node) => { updateTask(node.dataset.split, { status: "待派发", splitDone: true }); setSelected(node.dataset.split); AppRouter.navigate("manager-task-detail", { taskId: node.dataset.split }); });
    ctx.delegate("[data-dispatch]", "click", (_, node) => { updateTask(node.dataset.dispatch, { status: "已派发", assignee: "运营 A", review: "未提交" }); AppRouter.schedule("manager-dispatch"); });
    ctx.delegate("[data-review]", "click", (_, node) => { updateTask(node.dataset.review, { status: "待复核", review: "待复核" }); AppRouter.navigate("manager-review"); });
    ctx.delegate("[data-recap]", "click", (_, node) => { updateTask(node.dataset.recap, { recap: "已写入复盘", status: "已归档" }); AppRouter.schedule("manager-recap"); });
    ctx.delegate("[data-go]", "click", (_, node) => AppRouter.navigate(node.dataset.go));
  }

  window.ManagerTasksPage = { route: "manager-tasks", title: "店群任务", render() { const list = tasks(); return `${hero("STORE GROUP TASKS", "店群任务", "承接老板复盘审计任务、系统预警任务和经营模块任务，按时间、优先级、来源和状态排序。", "任务池", list.length)}${metricGrid([["老板下发", list.filter(x => x.source === "老板复盘审计").length, "复盘审计来源"], ["系统预警", list.filter(x => x.source === "系统预警").length, "经营异常来源"], ["待拆分", list.filter(x => x.status === "待拆分").length, "需要总管拆解"], ["待复核", list.filter(x => x.status === "待复核").length, "运营已提交"]])}<section class="page-section manager-section"><div class="section-header"><h3>店群任务池</h3><button type="button" data-go="manager-dispatch">进入任务派发</button></div>${sortBar()}${taskCards(list)}</section>`; }, mount: managerMount };
  window.ManagerDispatchPage = { route: "manager-dispatch", title: "任务派发", render() { const list = tasks(); return `${hero("TASK DISPATCH", "任务派发", "先拆分老板任务，再选择运营、截止时间、复核标准和复盘归档口径。", "待派发", list.filter(x => x.assignee === "待派发" || x.status === "待派发").length)}${metricGrid([["待派发", list.filter(x => x.assignee === "待派发" || x.status === "待派发").length, "需要指定运营"], ["已派发", list.filter(x => x.assignee !== "待派发").length, "责任已落位"], ["可承接", operators.filter(x => x.state === "可承接").length, "运营空闲"], ["高优先级", list.filter(x => x.priority === "高").length, "优先拆分"]])}<section class="page-section manager-section"><div class="section-header"><h3>运营负荷</h3><span class="status-badge">LOAD</span></div>${operatorCards()}</section><section class="page-section manager-section"><div class="section-header"><h3>待派发任务</h3><span class="status-badge">DISPATCH</span></div>${sortBar()}${taskCards(list.filter(x => x.assignee === "待派发" || x.status === "待派发" || x.status === "待拆分"))}</section>`; }, mount: managerMount };
  window.ManagerReviewPage = { route: "manager-review", title: "运营复核", render() { const review = tasks().filter(x => x.review === "待复核" || x.status === "待复核"); return `${hero("OPERATION REVIEW", "运营复核", "总管复核运营提交结果，判断是否通过、退回补充，或进入日报 / 周报复盘。", "待复核", review.length)}${metricGrid([["待复核", review.length, "需要总管确认"], ["已退回", 1, "需补充证据"], ["今日完成", 4, "团队产出"], ["需写复盘", tasks().filter(x => x.recap.includes("进入")).length, "沉淀报告"]])}<section class="page-section manager-section"><div class="section-header"><h3>复核队列</h3><span class="status-badge">REVIEW</span></div>${taskCards(review.length ? review : tasks().slice(0, 2))}</section>`; }, mount: managerMount };
  window.ManagerTaskDetailPage = { route: "manager-task-detail", title: "任务详情", render(ctx) { return detailPage(selectedTask(ctx)); }, mount: managerMount };
  window.ManagerModulesPage = { route: "manager-modules", title: "经营模块", render() { return `${hero("OPERATION MODULES", "经营模块", "商品、竞品、上新、流量、售后、库存不再平铺在左侧，而是在这里作为总管查原因和拆任务的入口。", "模块", moduleSignals.length)}${metricGrid([["异常模块", moduleSignals.filter(x => x.abnormal > 0).length, "需要关注"], ["模块任务", moduleSignals.reduce((n,x)=>n+x.task,0), "已进入任务池"], ["最高异常", "流量", "ROAS 低"], ["售后关注", "退款率", "拼多多偏高"]])}<section class="page-section manager-section"><div class="section-header"><h3>经营模块入口</h3><span class="status-badge">MODULES</span></div>${moduleCards()}</section>`; } };
  window.ManagerRetrospectivePage = { route: "manager-retrospective", title: "复盘提交", render() { return `${hero("RETROSPECTIVE SUBMIT", "复盘提交", "总管提交日报、周报、月报和专项复盘，老板在复盘审计中接收并定下周期任务。", "待提交", recaps.filter(x => x.status.includes("待")).length)}${metricGrid([["日报", "待提交", "今日经营"], ["周报", "草稿中", "目标达成"], ["月报", "待补财务", "利润库存"], ["专项复盘", "待整理", "投流问题"]])}<section class="page-section manager-section"><div class="section-header"><h3>复盘提交队列</h3><span class="status-badge">SUBMIT</span></div>${recapCards()}</section>`; } };
  window.ManagerReportsPage = { route: "manager-reports", title: "数据报表", render() { return `${hero("DATA REPORTS", "数据报表", "数据报表服务于总管写复盘：订单、投流、售后、库存和任务闭环都要能作为日报 / 周报依据。", "报表", 5)}${metricGrid([["订单报表", "已同步", "店铺销售"], ["投流报表", "关注", "ROAS 低"], ["售后报表", "关注", "退款率"], ["库存报表", "待复核", "资金占用"]])}${table("复盘数据依据", ["报表", "状态", "用途", "下一步"], [["订单报表", "已同步", "日报 / 周报销售达成", "写入周报"], ["投流报表", "关注", "ROAS 和消耗判断", "生成专项复盘"], ["售后报表", "关注", "退款和差评判断", "进入日报"], ["库存报表", "待复核", "库存资金占用", "进入月报"]])}`; } };
})();