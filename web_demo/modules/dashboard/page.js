(function () {
  const s = (value) => AppShell.escape(value);

  function timeLabel(date = new Date()) {
    const weeks = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
    return `${date.getMonth() + 1}月${date.getDate()}日 ${weeks[date.getDay()]} · ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")} 更新`;
  }

  const storeMap = {
    S001: { name: "家居生活主店", platform: "淘宝", sales: 42800, orders: 236, product: 126, traffic: "稳定", issue: "主推款需补库存" },
    S002: { name: "家居百货店", platform: "拼多多", sales: 35600, orders: 318, product: 98, traffic: "退款率偏高", issue: "售后差评需处理" },
    S003: { name: "家居好物号", platform: "抖音小店", sales: 29800, orders: 152, product: 64, traffic: "ROAS 偏低", issue: "短视频投流需复查" },
  };

  const ownerMetrics = [["今日销售额", "¥108,200", "跨平台汇总"], ["今日利润", "¥20,100", "预估毛利"], ["今日订单", "706", "淘宝 / 拼多多 / 抖音"], ["库存资金", "¥426,000", "现金占用"], ["广告消耗", "¥37,600", "投流成本"], ["退款率", "5.1%", "售后观察"], ["待审计问题", "4", "复盘审计"], ["待确认复盘", "3", "日报 / 周报 / 月报"]];
  const ownerModules = [
    { route: "store-overview", title: "店群总览", tag: "经营盘面", text: "平台、店铺、商品、订单、利润、评论、退款和库存。", signal: "拼多多退款率需关注" },
    { route: "task-command", title: "人员总览", tag: "人效状态", text: "员工在线、任务负荷、复核卡点和当前承接能力。", signal: "总管复核节奏需看" },
    { route: "profit-budget", title: "供投财务", tag: "货流钱", text: "供应链、投流、广告费、库存资金和利润健康度。", signal: "抖音 ROAS 偏低" },
    { route: "org-efficiency", title: "组织效率", tag: "组织权限", text: "职位关系、账号权限、店铺授权和组织配置。", signal: "暂无权限异常" },
    { route: "review-audit", title: "复盘审计", tag: "周期决策", text: "日报、周报、月报、审计问题和下周期任务草案。", signal: "周报未达标待确认" },
  ];
  const ownerFocus = [
    { title: "周报目标未达标", route: "review-audit", module: "复盘审计", reason: "本周销售达成率 90.6%，需要确认下周目标拆解。" },
    { title: "抖音 ROAS 偏低", route: "profit-budget", module: "供投财务", reason: "抖音 ROAS 1.8，低于目标 2.5，需要看投流和利润。" },
    { title: "拼多多退款率上升", route: "store-overview", module: "店群总览", reason: "拼多多退款率 5.8%，需要看店铺和商品口碑。" },
    { title: "总管复核节奏偏慢", route: "task-command", module: "人员总览", reason: "2 条任务接近超时，需要看人员负荷和复核卡点。" },
  ];

  function taskMetrics(tasks) { return [["紧急任务", tasks.filter((task) => task.priority === "高").length, "优先处理"], ["今日到期", tasks.filter((task) => String(task.deadline || "").includes("今天")).length, "有时间限制"], ["待确认", tasks.filter((task) => task.status === "待确认").length, "确认前不执行"], ["来源模块", new Set(tasks.map((task) => task.sourceModule)).size, "跨模块联动"]]; }
  function managerMetrics(tasks) { return [["老板下发", 1, "复盘审计来源"], ["待拆分", Math.max(1, tasks.filter((task) => !task.assigneeId).length), "需要总管处理"], ["已派发", tasks.filter((task) => task.assigneeId).length || 2, "责任已落位"], ["处理中", tasks.filter((task) => task.workflowStatus === "处理中").length || 2, "运营执行"], ["待复核", tasks.filter((task) => task.status === "待复核").length || 1, "总管确认"], ["逾期", 0, "当前无严重逾期"], ["今日完成", 4, "团队产出"], ["需写入复盘", 3, "日报 / 周报"]]; }
  function money(value) { return `¥${Number(value || 0).toLocaleString("zh-CN")}`; }
  function currentStores(user) { const ids = user?.storeIds?.length ? user.storeIds : ["S001"]; return ids.map((id) => ({ id, ...(storeMap[id] || { name: id, platform: "授权店铺", sales: 0, orders: 0, product: 0, traffic: "待同步", issue: "待同步" }) })); }

  function taskRow(task, index) {
    return `<article class="dashboard-task-card dashboard-linked-task dashboard-schedule-row"><div class="task-rank">${index + 1}</div><div class="dashboard-schedule-time"><span>${s(task.priority)}</span><strong>${s(task.deadline)}</strong></div><div class="dashboard-schedule-main"><div class="dashboard-linked-thumb">${s(task.imageLabel || "任")}</div><div class="dashboard-schedule-copy"><div class="dashboard-schedule-title-line"><h3>${s(task.taskType || "经营任务")}</h3><span>${s(task.taskSignal || task.status)}</span></div><strong>${s(task.productShort || task.title)}</strong><small>${s(task.productId || task.id)} · ${s(task.platform || "经营单元")} · ${s(task.store || "任务池")}</small></div></div><div class="dashboard-schedule-source"><span>来源</span><strong>${s(task.source || task.sourceModule)}</strong><small>${s(task.sourceModule || "统一任务池")}</small></div><div class="dashboard-schedule-judgment"><span>判断</span>${AppShell.tags(task.judgmentTags || [])}</div><div class="dashboard-linked-actions"><button type="button" data-go="business-actions">进入待办</button><button type="button" data-go="${s(task.sourceRoute || "business-actions")}">查看来源</button><button type="button" class="ghost" data-complete="${s(task.id)}">完成</button></div></article>`;
  }

  function ownerModuleCard(item) { return `<article class="owner-module-card"><div><span>${s(item.tag)}</span><h3>${s(item.title)}</h3><p>${s(item.text)}</p><small>${s(item.signal)}</small></div><button type="button" data-owner-go="${s(item.route)}">进入</button></article>`; }
  function ownerFocusCard(item) { return `<article class="owner-focus-card"><div><strong>${s(item.title)}</strong><p>${s(item.reason)}</p><span>${s(item.module)}</span></div><button type="button" data-owner-go="${s(item.route)}">查看详情</button></article>`; }
  function ownerDashboard() { return `<section class="owner-hero"><div><p class="eyebrow">OWNER BUSINESS OVERVIEW</p><h2>经营总览</h2><p>老板首页只看经营摘要和决策入口，不处理单条任务。任务拆分、派发和复核交给店群总管。</p><small>${timeLabel()}</small></div><div class="owner-hero-side"><span>今日状态</span><strong>经营正常 · 4 项需关注</strong><small>从盘面进入模块，从复盘形成下周期任务</small></div></section><section class="kpi-grid owner-metrics">${ownerMetrics.map(([label, value, desc]) => AppShell.metricCard(label, value, desc)).join("")}</section><section class="page-section owner-section"><div class="section-header"><div><h3>老板模块入口</h3><span class="status-badge">经营 / 人员 / 供投 / 组织 / 复盘</span></div></div><div class="owner-module-grid">${ownerModules.map(ownerModuleCard).join("")}</div></section><section class="page-section owner-section"><div class="section-header"><div><h3>今日老板关注</h3><span class="status-badge">只看判断入口，不做任务完成</span></div></div><div class="owner-focus-list">${ownerFocus.map(ownerFocusCard).join("")}</div></section>`; }

  function managerScheduleRow(item, index) {
    return `<article class="manager-schedule-row"><div class="manager-schedule-rank">${index + 1}</div><div class="manager-schedule-time"><span>${s(item.priority)}</span><strong>${s(item.due)}</strong></div><div class="manager-schedule-main"><div class="manager-schedule-icon">${s(item.icon || "任")}</div><div><div class="manager-schedule-title"><h3>${s(item.title)}</h3><span>${s(item.state)}</span></div><strong>${s(item.target)}</strong><small>${s(item.id)} · ${s(item.assignee)} · ${s(item.recap)}</small></div></div><div class="manager-schedule-source"><span>来源</span><strong>${s(item.source)}</strong><small>${s(item.sourceReport)}</small></div><div class="manager-schedule-judgment"><span>判断</span><div class="manager-task-meta compact">${item.tags.map((tag) => `<span>${s(tag)}</span>`).join("")}</div></div><div class="manager-schedule-actions"><button type="button" data-manager-detail="${s(item.id)}">查看详情</button><button type="button" class="secondary" data-go="manager-dispatch">拆分 / 派发</button><button type="button" class="secondary" data-go="manager-review">进入复核</button></div></article>`;
  }

  function managerDashboard(active) {
    const rows = [
      { id: "MT-001", source: "老板复盘审计", sourceReport: "本周周报", title: "抖音低 ROAS 商品预算收缩", target: "抖音小店", assignee: "待派发", due: "下周", priority: "高", state: "待拆分", recap: "进入周报", icon: "投", tags: ["ROAS 低", "预算收缩", "需拆分"] },
      { id: "MT-002", source: "系统预警", sourceReport: "售后预警", title: "拼多多退款率商品专项复查", target: "家居百货店", assignee: "运营 B", due: "今天 18:00", priority: "中", state: "处理中", recap: "进入日报", icon: "售", tags: ["退款率高", "售后复查", "进日报"] },
      { id: "MT-003", source: "经营模块", sourceReport: "商品 / 售后", title: "厨房置物架售后优先处理", target: "厨房置物架", assignee: "运营 A", due: "今天 20:00", priority: "高", state: "待复核", recap: "进入日报", icon: "架", tags: ["待复核", "售后优先", "进日报"] },
    ];
    return `<section class="dashboard-status dashboard-linked-board"><div class="dashboard-status-main"><p class="eyebrow">MANAGER EXECUTION BOARD</p><h2>店群执行总览</h2><p class="dashboard-time">${timeLabel()}</p></div><div class="dashboard-status-side"><span>总管职责</span><strong>承接 · 拆分 · 复核 · 复盘</strong><small>老板任务 → 运营动作 → 周期复盘</small></div></section><section class="kpi-grid dashboard-metrics dashboard-linked-metrics">${managerMetrics(active).map(([label, value, desc]) => AppShell.metricCard(label, value, desc)).join("")}</section><section class="page-section manager-section"><div class="section-header"><div><h3>今日处理顺序</h3><span class="status-badge">老板任务 / 系统预警 / 经营模块</span></div><button type="button" data-go="manager-tasks">查看店群任务</button></div><div class="manager-sort-bar manager-sort-bar-light"><button type="button" data-go="manager-tasks">按时间排序</button><button type="button" data-go="manager-tasks">按优先级排序</button><button type="button" data-go="manager-tasks">按来源排序</button></div><div class="manager-schedule-list">${rows.map(managerScheduleRow).join("")}</div></section>`;
  }

  function operatorModuleCard(item) { return `<article class="operator-module-card"><div><span>${s(item.tag)}</span><h3>${s(item.title)}</h3><p>${s(item.text)}</p></div><button type="button" data-go="${s(item.route)}">进入</button></article>`; }
  function operatorStoreCard(store) { return `<article class="operator-store-card"><div class="operator-store-head"><strong>${s(store.name)}</strong><span>${s(store.platform)}</span></div><div class="operator-store-metrics"><div><b>${store.product}</b><small>商品</small></div><div><b>${store.orders}</b><small>订单</small></div><div><b>${money(store.sales)}</b><small>销售额</small></div></div><p>${s(store.issue)} · 流量状态：${s(store.traffic)}</p></article>`; }
  function operatorDashboard(active, user) {
    const stores = currentStores(user);
    const sales = stores.reduce((sum, item) => sum + item.sales, 0);
    const orders = stores.reduce((sum, item) => sum + item.orders, 0);
    const modules = [
      { route: "operating-unit", title: "经营单元", tag: "我的店铺", text: "看自己被授权店铺的经营状态和异常。" },
      { route: "data-check", title: "报表", tag: "ERP / CRM", text: "查看负责店铺的订单、售后、库存、投流报表。" },
      { route: "business-products", title: "商品", tag: "商品运营", text: "处理负责店铺的商品问题和商品任务。" },
      { route: "business-competitors", title: "竞品", tag: "竞品观察", text: "跟进负责类目的竞品价格和卖点变化。" },
      { route: "business-listing", title: "上新", tag: "上架执行", text: "管理新商品素材、标题、价格和上架节奏。" },
      { route: "business-traffic", title: "流量", tag: "投流承接", text: "检查负责店铺的流量、ROI 和投放异常。" },
    ];
    return `<section class="operator-hero"><div><p class="eyebrow">STORE OPERATOR OVERVIEW</p><h2>我的店铺经营总览</h2><p>${s(user?.name || "运营")}只看被分配店铺的经营单元、报表、商品、竞品、上新、流量、待办和日志。</p><small>负责店铺：${stores.map((item) => `${item.platform} · ${item.name}`).join(" / ")} · ${timeLabel()}</small></div><div class="operator-hero-side"><span>数据范围</span><strong>授权店铺</strong><small>不是公司全部店铺</small></div></section><section class="kpi-grid operator-metrics">${[["负责店铺", stores.length, "授权范围"], ["今日销售额", money(sales), "我的店铺"], ["今日订单", orders, "我的店铺"], ["商品数", stores.reduce((sum, item) => sum + item.product, 0), "负责商品"], ["待办", active.length, "我的任务"], ["日志", 2, "今日待提交"], ["异常", stores.filter((item) => item.traffic !== "稳定").length, "需处理"], ["上新", 3, "本周计划"]].map(([label, value, desc]) => AppShell.metricCard(label, value, desc)).join("")}</section><section class="page-section operator-section"><div class="section-header"><div><h3>负责店铺</h3><span class="status-badge">只显示授权范围</span></div></div><div class="operator-store-grid">${stores.map(operatorStoreCard).join("")}</div></section><section class="page-section operator-section"><div class="section-header"><div><h3>运营模块入口</h3><span class="status-badge">经营单元 / 报表 / 商品 / 竞品 / 上新 / 流量</span></div></div><div class="operator-module-grid">${modules.map(operatorModuleCard).join("")}</div></section><section class="page-section dashboard-queue dashboard-linked-queue"><div class="section-header dashboard-linked-header"><div><h3>我的待办</h3><span class="status-badge">只看分配给当前运营的任务</span></div><button type="button" data-go="business-actions">查看全部待办</button></div><section class="dashboard-task-list dashboard-schedule-list">${active.length ? AppTaskStore.listDashboardTasks().map(taskRow).join("") : `<article class="dashboard-empty">当前没有待处理任务。</article>`}</section></section>`;
  }

  window.DashboardPage = {
    route: "dashboard",
    title: "总览",
    render() {
      const user = AppApi.currentUser?.();
      const active = AppTaskStore.listActiveTasks();
      if (user?.roleId === "owner") return ownerDashboard();
      if (user?.roleId === "manager") return managerDashboard(active);
      if (user?.roleId === "operator") return operatorDashboard(active, user);
      const top = AppTaskStore.listDashboardTasks();
      return `<section class="dashboard-status dashboard-linked-board"><div class="dashboard-status-main"><p class="eyebrow">COMMAND BOARD · MODULED</p><h2>任务清单</h2><p class="dashboard-time">${timeLabel()}</p></div><div class="dashboard-status-side"><span>前端架构</span><strong>模块注册制</strong><small>首页 · 待办 · 日志同步</small></div></section><section class="kpi-grid dashboard-metrics dashboard-linked-metrics">${taskMetrics(active).map(([label, value, desc]) => AppShell.metricCard(label, value, desc)).join("")}</section><section class="page-section dashboard-queue dashboard-linked-queue"><div class="section-header dashboard-linked-header"><div><h3>处理顺序</h3><span class="status-badge">任务池 / 时间 / 判断</span></div><button type="button" data-go="business-actions">查看全部待办</button></div><section class="dashboard-task-list dashboard-schedule-list">${top.length ? top.map(taskRow).join("") : `<article class="dashboard-empty">当前没有待处理任务。</article>`}</section></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-go]", "click", (_, node) => AppRouter.navigate(node.dataset.go));
      ctx.delegate("[data-owner-go]", "click", (_, node) => AppRouter.navigate(node.dataset.ownerGo));
      ctx.delegate("[data-manager-detail]", "click", (_, node) => { localStorage.setItem("manager_selected_task_v241", node.dataset.managerDetail); AppRouter.navigate("manager-task-detail", { taskId: node.dataset.managerDetail }); });
      ctx.delegate("[data-complete]", "click", (_, node) => { AppTaskStore.completeTask(node.dataset.complete); AppRouter.schedule("task-complete"); });
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();