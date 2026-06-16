(function () {
  function timeLabel(date = new Date()) {
    const weeks = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
    return `${date.getMonth() + 1}月${date.getDate()}日 ${weeks[date.getDay()]} · ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")} 更新`;
  }

  function metrics(tasks) {
    return [
      ["紧急任务", tasks.filter((task) => task.priority === "高").length, "优先处理"],
      ["今日到期", tasks.filter((task) => String(task.deadline || "").includes("今天")).length, "有时间限制"],
      ["待确认", tasks.filter((task) => task.status === "待确认").length, "确认前不执行"],
      ["来源模块", new Set(tasks.map((task) => task.sourceModule)).size, "跨模块联动"],
    ];
  }

  function taskRow(task, index) {
    return `<article class="dashboard-task-card dashboard-linked-task dashboard-schedule-row">
      <div class="task-rank">${index + 1}</div>
      <div class="dashboard-schedule-time"><span>${AppShell.escape(task.priority)}</span><strong>${AppShell.escape(task.deadline)}</strong></div>
      <div class="dashboard-schedule-main"><div class="dashboard-linked-thumb">${AppShell.escape(task.imageLabel || "任")}</div><div class="dashboard-schedule-copy"><div class="dashboard-schedule-title-line"><h3>${AppShell.escape(task.taskType || "经营任务")}</h3><span>${AppShell.escape(task.taskSignal || task.status)}</span></div><strong>${AppShell.escape(task.productShort || task.title)}</strong><small>${AppShell.escape(task.productId || task.id)} · ${AppShell.escape(task.platform || "经营单元")} · ${AppShell.escape(task.store || "任务池")}</small></div></div>
      <div class="dashboard-schedule-source"><span>来源</span><strong>${AppShell.escape(task.source || task.sourceModule)}</strong><small>${AppShell.escape(task.sourceModule || "统一任务池")}</small></div>
      <div class="dashboard-schedule-judgment"><span>判断</span>${AppShell.tags(task.judgmentTags || [])}</div>
      <div class="dashboard-linked-actions"><button type="button" data-go="business-actions">进入待办</button><button type="button" data-go="${AppShell.escape(task.sourceRoute || "business-actions")}">查看来源</button><button type="button" class="ghost" data-complete="${AppShell.escape(task.id)}">完成</button></div>
    </article>`;
  }

  window.DashboardPage = {
    route: "dashboard",
    title: "总览",
    render() {
      const active = AppTaskStore.listActiveTasks();
      const top = AppTaskStore.listDashboardTasks();
      return `<section class="dashboard-status dashboard-linked-board"><div class="dashboard-status-main"><p class="eyebrow">COMMAND BOARD · MODULED</p><h2>任务清单</h2><p class="dashboard-time">${timeLabel()}</p></div><div class="dashboard-status-side"><span>前端架构</span><strong>模块注册制</strong><small>首页 · 待办 · 日志同步</small></div></section>
      <section class="kpi-grid dashboard-metrics dashboard-linked-metrics">${metrics(active).map(([label, value, desc]) => AppShell.metricCard(label, value, desc)).join("")}</section>
      <section class="page-section dashboard-queue dashboard-linked-queue"><div class="section-header dashboard-linked-header"><div><h3>处理顺序</h3><span class="status-badge">任务池 / 时间 / 判断</span></div><button type="button" data-go="business-actions">查看全部待办</button></div><section class="dashboard-task-list dashboard-schedule-list">${top.length ? top.map(taskRow).join("") : `<article class="dashboard-empty">当前没有待处理任务。</article>`}</section></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-go]", "click", (_, node) => AppRouter.navigate(node.dataset.go));
      ctx.delegate("[data-complete]", "click", (_, node) => { AppTaskStore.completeTask(node.dataset.complete); AppRouter.schedule("task-complete"); });
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();
