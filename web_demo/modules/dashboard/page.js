(function () {
  const s = (value) => AppShell.escape(value ?? "");

  function localFallback() {
    const v3 = window.AppMockData?.v3 || {};
    const tasks = AppTaskStore.listActiveTasks().filter((task) => task.displayState !== "backend_only" && !["backend_tag", "store_product_tag"].includes(task.queueType)).map((task, index) => normalizeTask(task, index + 1));
    const highRisk = tasks.filter((task) => task.priority === "高" || task.priorityLevel === "danger").slice(0, 3);
    const review = tasks.filter((task) => ["待复核", "已提交"].includes(task.status)).slice(0, 3);
    return {
      hasData: Boolean(v3.latestDataVersion || tasks.length || (window.AppMockData.products || []).length),
      title: "今日任务台",
      heroBadge: tasks.length ? `${tasks.length} 个优先任务` : "数据已同步",
      latestImport: { label: "最新数据", status: v3.latestDataVersion ? "已同步" : "待同步", totalRows: 0, importedCount: 0, affectedModules: [] },
      metrics: [
        { label: "优先任务", value: tasks.length, desc: "今日先处理" },
        { label: "高风险", value: highRisk.length, desc: "执行队列" },
        { label: "待复核", value: review.length, desc: "等待确认" },
        { label: "完成率", value: "0%", desc: "任务进度" },
      ],
      taskQueue: tasks,
      todayWorkbench: {
        mode: "v11_1_today_task_workbench",
        todayPriorityTasks: tasks.slice(0, 5),
        highRiskItems: highRisk,
        pendingReviewItems: review,
        emptyPriorityText: "当前无需要立即处理的高风险任务，低风险信号已沉淀为商品 / 店铺标签。",
        latestReportResult: { label: "最新数据", status: v3.latestDataVersion ? "已同步" : "待同步", summary: v3.latestDataVersion ? "经营数据、商品标签、店铺权重和任务队列已更新。" : "上传报表后自动清洗、入库并生成标签。", taskHint: `${tasks.length} 个执行任务`, latestSyncedAt: "已同步" },
        completionProgress: { visibleActive: tasks.length, processing: 0, pendingReview: review.length, returned: 0, completed: 0, completionRate: 0, summary: `当前执行任务 ${tasks.length} 个` },
      },
    };
  }

  function normalizeTask(task, rank) {
    const product = task.productId || task.entityId || task.productShort || "任务";
    const domain = task.riskDomain || task.taskType || "经营";
    const signal = task.taskSignal || task.actionType || "处理";
    return { rank, id: task.id, title: task.title && task.title !== task.taskType ? task.title : `${product}｜${domain}｜${signal}`, riskDomain: domain, priority: task.priority || "中", priorityLevel: task.priorityLevel || "warning", deadline: task.deadline || "本周内", status: task.workflowStatus || task.status || "待处理", source: task.source || task.sourceModule || "任务池", reason: task.reason || task.task || "由导入数据生成。", assigneeName: task.assigneeName || "未派发" };
  }

  function metricCard(item) {
    return `<article class="card report-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong>${item.desc ? `<small>${s(item.desc)}</small>` : ""}</article>`;
  }

  function taskRow(task) {
    return `<article class="dashboard-task-card dashboard-schedule-row"><div class="todo-rank ${AppShell.statusClass(task.priorityLevel)}">${s(task.rank)}</div><div class="dashboard-schedule-time"><strong>${s(task.deadline)}</strong></div><div class="dashboard-schedule-main"><span class="dashboard-linked-thumb">${s(task.riskDomain?.[0] || "任")}</span><div class="dashboard-schedule-copy"><div class="dashboard-schedule-title-line"><h3>${s(task.title)}</h3><span>${s(task.priority)}</span></div><strong>${s(task.reason)}</strong><small>${s(task.source)} · ${s(task.status)}</small></div></div><div class="dashboard-linked-actions"><button type="button" data-open-task="${s(task.id)}">处理任务</button></div></article>`;
  }

  function compactItem(task) {
    return `<article class="dashboard-compact-item"><strong>${s(task.title)}</strong><span>${s(task.priority)} · ${s(task.status)} · ${s(task.deadline)}</span><button type="button" data-open-task="${s(task.id)}">处理</button></article>`;
  }

  function reportResult(report) {
    if (!report) return "";
    return `<section class="v102-status-strip dashboard-report-result"><strong>${s(report.status)}</strong><span>${s(report.label)}</span><span>${s(report.summary)}</span><button type="button" class="secondary" data-open-report>报表</button></section>`;
  }

  function completionCard(progress = {}) {
    return `<section class="page-section dashboard-progress-card"><div class="section-header"><h3>今日完成进度</h3><span class="status-badge">${s(progress.completionRate ?? 0)}%</span></div><div class="dashboard-progress-grid"><article><span>执行任务</span><strong>${s(progress.visibleActive ?? 0)}</strong></article><article><span>处理中</span><strong>${s(progress.processing ?? 0)}</strong></article><article><span>待复核</span><strong>${s(progress.pendingReview ?? 0)}</strong></article><article><span>已完成</span><strong>${s(progress.completed ?? 0)}</strong></article></div><p>${s(progress.summary || "任务完成后进入日志沉淀。")}</p></section>`;
  }

  function sideSection(title, items, emptyText) {
    return `<section class="page-section dashboard-side-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${items.length}</span></div><div class="dashboard-compact-list">${items.length ? items.map(compactItem).join("") : `<div class="dashboard-empty">${s(emptyText)}</div>`}</div></section>`;
  }

  function renderDashboard(payload) {
    if (!payload?.hasData) return `<section class="v102-hero owner-hero"><div><h2>今日任务台</h2><strong>上传报表后，系统会清洗数据、生成标签并同步任务队列。</strong></div><div class="v102-primary-action"><button type="button" data-open-report>上传报表</button><span>先导入数据</span></div></section>`;
    const metrics = payload.metrics || [];
    const workbench = payload.todayWorkbench || {};
    const priorityTasks = workbench.todayPriorityTasks || payload.taskQueue || [];
    const highRisk = workbench.highRiskItems || [];
    const reviewItems = workbench.pendingReviewItems || [];
    const emptyText = workbench.emptyPriorityText || "当前无需要立即处理的高风险任务，低风险信号已沉淀为商品 / 店铺标签。";
    return `<section class="v102-hero owner-hero"><div><h2>今日任务台</h2><strong>先处理执行任务，再查看经营数据。</strong></div><div class="v102-primary-action"><button type="button" data-open-tasks>${priorityTasks.length ? "处理任务" : "查看任务"}</button><span>${s(payload.heroBadge || `${priorityTasks.length} 个优先任务`)}</span></div></section>
      <section class="kpi-grid owner-metrics dashboard-workbench-metrics">${metrics.map(metricCard).join("")}</section>
      ${reportResult(workbench.latestReportResult)}
      <section class="dashboard-workbench-grid">
        <section class="page-section dashboard-queue dashboard-linked-queue v102-main-section dashboard-priority-section"><div class="section-header"><h3>今日优先任务</h3><span class="status-badge">${priorityTasks.length} 个</span></div><div class="dashboard-task-list">${priorityTasks.length ? priorityTasks.map(taskRow).join("") : `<div class="dashboard-empty">${s(emptyText)}</div>`}</div></section>
        <div class="dashboard-workbench-side">
          ${sideSection("高风险事项", highRisk, "暂无高风险执行事项。")}
          ${sideSection("待复核事项", reviewItems, "暂无待复核事项。")}
          ${completionCard(workbench.completionProgress)}
        </div>
      </section>`;
  }

  window.DashboardPage = {
    route: "dashboard",
    title: "总览",
    async render() {
      const payload = await AppApi.dashboard() || localFallback();
      return renderDashboard(payload);
    },
    mount(ctx) {
      ctx.delegate("[data-open-task]", "click", (_, node) => node.dataset.openTask ? AppTaskActions.openTodoTask(node.dataset.openTask) : AppRouter.navigate("business-actions"));
      ctx.delegate("[data-open-tasks]", "click", () => AppRouter.navigate("business-actions"));
      ctx.delegate("[data-open-report]", "click", () => AppRouter.navigate("data-check"));
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();