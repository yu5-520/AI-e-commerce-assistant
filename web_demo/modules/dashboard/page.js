(function () {
  function timeLabel(date = new Date()) {
    const weeks = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
    return `${date.getMonth() + 1}月${date.getDate()}日 ${weeks[date.getDay()]} · ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")} 更新`;
  }

  function metrics(tasks) {
    return [["紧急任务", tasks.filter((task) => task.priority === "高").length, "优先处理"], ["今日到期", tasks.filter((task) => String(task.deadline || "").includes("今天")).length, "有时间限制"], ["待确认", tasks.filter((task) => task.status === "待确认").length, "确认前不执行"], ["来源模块", new Set(tasks.map((task) => task.sourceModule)).size, "跨模块联动"]];
  }

  function managerMetrics(tasks) {
    return [["老板下发", 1, "复盘审计来源"], ["待拆分", Math.max(1, tasks.filter((task) => !task.assigneeId).length), "需要总管处理"], ["已派发", tasks.filter((task) => task.assigneeId).length || 2, "责任已落位"], ["处理中", tasks.filter((task) => task.workflowStatus === "处理中").length || 2, "运营执行"], ["待复核", tasks.filter((task) => task.status === "待复核").length || 1, "总管确认"], ["逾期", 0, "当前无严重逾期"], ["今日完成", 4, "团队产出"], ["需写入复盘", 3, "日报 / 周报"]];
  }

  function taskRow(task, index) {
    return `<article class="dashboard-task-card dashboard-linked-task dashboard-schedule-row"><div class="task-rank">${index + 1}</div><div class="dashboard-schedule-time"><span>${AppShell.escape(task.priority)}</span><strong>${AppShell.escape(task.deadline)}</strong></div><div class="dashboard-schedule-main"><div class="dashboard-linked-thumb">${AppShell.escape(task.imageLabel || "任")}</div><div class="dashboard-schedule-copy"><div class="dashboard-schedule-title-line"><h3>${AppShell.escape(task.taskType || "经营任务")}</h3><span>${AppShell.escape(task.taskSignal || task.status)}</span></div><strong>${AppShell.escape(task.productShort || task.title)}</strong><small>${AppShell.escape(task.productId || task.id)} · ${AppShell.escape(task.platform || "经营单元")} · ${AppShell.escape(task.store || "任务池")}</small></div></div><div class="dashboard-schedule-source"><span>来源</span><strong>${AppShell.escape(task.source || task.sourceModule)}</strong><small>${AppShell.escape(task.sourceModule || "统一任务池")}</small></div><div class="dashboard-schedule-judgment"><span>判断</span>${AppShell.tags(task.judgmentTags || [])}</div><div class="dashboard-linked-actions"><button type="button" data-go="business-actions">进入待办</button><button type="button" data-go="${AppShell.escape(task.sourceRoute || "business-actions")}">查看来源</button><button type="button" class="ghost" data-complete="${AppShell.escape(task.id)}">完成</button></div></article>`;
  }

  function managerRow(item, index) {
    return `<article class="manager-task-card"><div class="manager-task-top"><span class="status-dot ${item.state === "待复核" ? "watch" : item.state === "待拆分" ? "warning" : "good"}"></span><strong>${AppShell.escape(item.title)}</strong><b>${AppShell.escape(item.priority)}</b></div><div class="manager-task-meta"><span>来源：${AppShell.escape(item.source)}</span><span>负责人：${AppShell.escape(item.assignee)}</span><span>截止：${AppShell.escape(item.due)}</span><span>${AppShell.escape(item.recap)}</span></div><p>${index + 1}. ${AppShell.escape(item.state)} · ${AppShell.escape(item.note)}</p><div class="manager-action-row"><button type="button" data-manager-detail="${AppShell.escape(item.id)}">查看详情</button><button type="button" class="secondary" data-go="manager-dispatch">拆分 / 派发</button><button type="button" class="secondary" data-go="manager-review">进入复核</button></div></article>`;
  }

  function managerDashboard(active) {
    const rows = [
      { id: "MT-001", source: "老板复盘审计", title: "抖音低 ROAS 商品预算收缩", assignee: "待派发", due: "下周", priority: "高", state: "待拆分", recap: "进入周报", note: "先拆给运营 A 和数据财务" },
      { id: "MT-002", source: "系统预警", title: "拼多多退款率商品专项复查", assignee: "运营 B", due: "今天 18:00", priority: "中", state: "处理中", recap: "进入日报", note: "售后原因和差评商品待补充" },
      { id: "MT-003", source: "经营模块", title: "厨房置物架售后优先处理", assignee: "运营 A", due: "今天 20:00", priority: "高", state: "待复核", recap: "进入日报", note: "运营已提交，等待总管确认" },
    ];
    return `<section class="dashboard-status dashboard-linked-board"><div class="dashboard-status-main"><p class="eyebrow">MANAGER EXECUTION BOARD</p><h2>店群执行总览</h2><p class="dashboard-time">${timeLabel()}</p></div><div class="dashboard-status-side"><span>总管职责</span><strong>承接 · 拆分 · 复核 · 复盘</strong><small>老板任务 → 运营动作 → 周期复盘</small></div></section><section class="kpi-grid dashboard-metrics dashboard-linked-metrics">${managerMetrics(active).map(([label, value, desc]) => AppShell.metricCard(label, value, desc)).join("")}</section><section class="page-section manager-section"><div class="section-header"><div><h3>今日处理顺序</h3><span class="status-badge">老板任务 / 系统预警 / 经营模块</span></div><button type="button" data-go="manager-tasks">查看店群任务</button></div><div class="manager-sort-bar"><button type="button" data-go="manager-tasks">按时间排序</button><button type="button" data-go="manager-tasks">按优先级排序</button><button type="button" data-go="manager-tasks">按来源排序</button></div><div class="manager-task-list">${rows.map(managerRow).join("")}</div></section>`;
  }

  window.DashboardPage = {
    route: "dashboard",
    title: "总览",
    render() {
      const user = AppApi.currentUser?.();
      const active = AppTaskStore.listActiveTasks();
      if (user?.roleId === "manager") return managerDashboard(active);
      const top = AppTaskStore.listDashboardTasks();
      return `<section class="dashboard-status dashboard-linked-board"><div class="dashboard-status-main"><p class="eyebrow">COMMAND BOARD · MODULED</p><h2>任务清单</h2><p class="dashboard-time">${timeLabel()}</p></div><div class="dashboard-status-side"><span>前端架构</span><strong>模块注册制</strong><small>首页 · 待办 · 日志同步</small></div></section><section class="kpi-grid dashboard-metrics dashboard-linked-metrics">${metrics(active).map(([label, value, desc]) => AppShell.metricCard(label, value, desc)).join("")}</section><section class="page-section dashboard-queue dashboard-linked-queue"><div class="section-header dashboard-linked-header"><div><h3>处理顺序</h3><span class="status-badge">任务池 / 时间 / 判断</span></div><button type="button" data-go="business-actions">查看全部待办</button></div><section class="dashboard-task-list dashboard-schedule-list">${top.length ? top.map(taskRow).join("") : `<article class="dashboard-empty">当前没有待处理任务。</article>`}</section></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-go]", "click", (_, node) => AppRouter.navigate(node.dataset.go));
      ctx.delegate("[data-manager-detail]", "click", (_, node) => { localStorage.setItem("manager_selected_task_v239", node.dataset.managerDetail); AppRouter.navigate("manager-task-detail", { taskId: node.dataset.managerDetail }); });
      ctx.delegate("[data-complete]", "click", (_, node) => { AppTaskStore.completeTask(node.dataset.complete); AppRouter.schedule("task-complete"); });
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();