(function () {
  const s = (value) => AppShell.escape(value);
  function hasData() {
    const v3 = window.AppMockData?.v3 || {};
    return Boolean(v3.latestDataVersion || v3.activeAlertCount || (window.AppMockData.products || []).length || (window.AppMockData.traffic || []).length || AppTaskStore.listActiveTasks().length);
  }
  function taskRow(task) { return `<article class="dashboard-task-card"><strong>${s(task.taskType || task.title)}</strong><button type="button" data-go="business-actions">进入待办</button></article>`; }
  function renderShell(empty) {
    if (empty) return `<section class="owner-hero"><div><h2>暂无数据</h2></div><div class="owner-hero-side"><strong>V5</strong></div></section>`;
    const v3 = window.AppMockData?.v3 || {};
    const tasks = AppTaskStore.listActiveTasks();
    const metrics = [["数据版本", v3.latestDataVersion || "—", ""], ["预警", v3.activeAlertCount || 0, ""], ["商品", (window.AppMockData.products || []).length, ""], ["任务", tasks.length, ""]];
    return `<section class="owner-hero"><div><h2>经营总览</h2></div><div class="owner-hero-side"><strong>${s(v3.latestDataVersion || "V5")}</strong></div></section><section class="kpi-grid owner-metrics">${metrics.map(([label, value, desc]) => AppShell.metricCard(label, value, desc)).join("")}</section>${tasks.length ? `<section class="page-section dashboard-queue dashboard-linked-queue"><div class="section-header"><h3>当前任务</h3></div>${tasks.map(taskRow).join("")}</section>` : ""}`;
  }
  window.DashboardPage = { route: "dashboard", title: "总览", render() { return renderShell(!hasData()); }, mount(ctx) { ctx.delegate("[data-go]", "click", (_, node) => AppRouter.navigate(node.dataset.go)); ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store"))); } };
})();
