(function () {
  const s = (value) => AppShell.escape(value ?? "");

  function localFallback() {
    const v3 = window.AppMockData?.v3 || {};
    const tasks = AppTaskStore.listActiveTasks();
    return {
      hasData: Boolean(v3.latestDataVersion || tasks.length || (window.AppMockData.products || []).length),
      title: "经营总览",
      heroBadge: "已同步",
      latestImport: { label: "最新数据", status: v3.latestDataVersion ? "已入库" : "待导入", totalRows: 0, importedCount: 0, affectedModules: [] },
      metrics: [
        { label: "最新数据", value: v3.latestDataVersion ? "已同步" : "暂无", desc: v3.latestDataVersion ? "已入库" : "待导入" },
        { label: "报表", value: "0 条", desc: "等待导入" },
        { label: "商品", value: (window.AppMockData.products || []).length, desc: "已进入商品栏" },
        { label: "任务", value: tasks.length, desc: "当前待办" },
      ],
      taskQueue: tasks.map((task, index) => normalizeTask(task, index + 1)),
    };
  }

  function normalizeTask(task, rank) {
    const product = task.productId || task.entityId || task.productShort || "任务";
    const domain = task.riskDomain || task.taskType || "经营";
    const signal = task.taskSignal || task.actionType || "处理";
    return {
      rank,
      id: task.id,
      title: task.title && task.title !== task.taskType ? task.title : `${product}｜${domain}｜${signal}`,
      riskDomain: domain,
      priority: task.priority || "中",
      priorityLevel: task.priorityLevel || "warning",
      deadline: task.deadline || "本周内",
      status: task.workflowStatus || task.status || "待处理",
      source: task.source || task.sourceModule || "任务池",
      reason: task.reason || task.task || "由导入数据生成。",
    };
  }

  function metricCard(item) {
    return `<article class="card report-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong>${item.desc ? `<small>${s(item.desc)}</small>` : ""}</article>`;
  }

  function importSummary(latest) {
    if (!latest || latest.status === "待导入") return "";
    const modules = (latest.affectedModules || []).join(" / ") || "报表 / 总览";
    return `<section class="page-section dashboard-import-summary"><div class="section-header"><h3>最新导入</h3><span class="status-badge">${s(latest.status)}</span></div><div class="alert-kv-grid"><article><span>报表</span><strong>${s(latest.label)}</strong></article><article><span>记录</span><strong>${s(latest.totalRows || latest.rows || 0)} 条</strong></article><article><span>影响模块</span><strong>${s(modules)}</strong></article><article><span>同步时间</span><strong>${s(latest.latestSyncedAt || "已同步")}</strong></article></div></section>`;
  }

  function taskRow(task) {
    return `<article class="dashboard-task-card dashboard-schedule-row"><div class="todo-rank ${AppShell.statusClass(task.priorityLevel)}">${s(task.rank)}</div><div class="dashboard-schedule-time"><span>时限</span><strong>${s(task.deadline)}</strong></div><div class="dashboard-schedule-main"><span class="dashboard-linked-thumb">${s(task.riskDomain?.[0] || "任")}</span><div class="dashboard-schedule-copy"><div class="dashboard-schedule-title-line"><h3>${s(task.title)}</h3><span>${s(task.priority)}</span></div><strong>${s(task.reason)}</strong><small>${s(task.source)} · ${s(task.status)}</small></div></div><div class="dashboard-linked-actions"><button type="button" data-open-task="${s(task.id)}">进入待办</button></div></article>`;
  }

  function renderDashboard(payload) {
    if (!payload?.hasData) return `<section class="owner-hero"><div><h2>暂无数据</h2></div><div class="owner-hero-side"><strong>数据驱动</strong></div></section>`;
    const metrics = payload.metrics || [];
    const tasks = payload.taskQueue || [];
    return `<section class="owner-hero"><div><h2>经营总览</h2></div><div class="owner-hero-side"><strong>${s(payload.heroBadge || "已同步")}</strong></div></section><section class="kpi-grid owner-metrics">${metrics.map(metricCard).join("")}</section>${importSummary(payload.latestImport)}<section class="page-section dashboard-queue dashboard-linked-queue"><div class="section-header"><h3>当前任务</h3><span class="status-badge">按紧急程度和时间排序</span></div><div class="dashboard-task-list">${tasks.length ? tasks.map(taskRow).join("") : `<div class="dashboard-empty">当前没有可见待办。</div>`}</div></section>`;
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
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();
