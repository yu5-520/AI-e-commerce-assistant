(function () {
  const s = (value) => AppShell.escape(value);
  function hasData() {
    const v3 = window.AppMockData?.v3 || {};
    return Boolean(v3.latestDataVersion || v3.activeAlertCount || (window.AppMockData.products || []).length || (window.AppMockData.traffic || []).length || AppTaskStore.listActiveTasks().length);
  }
  function card(route, title) {
    return `<article class="owner-module-card"><div><span>模块</span><h3>${s(title)}</h3><p>保留原有功能，内容由导入数据生成。</p></div><button type="button" data-go="${s(route)}">进入</button></article>`;
  }
  function taskRow(task) {
    return `<article class="dashboard-task-card"><strong>${s(task.taskType || task.title)}</strong><p>${s(task.reason || task.task || "")}</p><button type="button" data-go="business-actions">进入待办</button></article>`;
  }
  function renderShell(empty) {
    const v3 = window.AppMockData?.v3 || {};
    const tasks = AppTaskStore.listActiveTasks();
    const metrics = [["数据版本", v3.latestDataVersion || "—", "报表模块"], ["活跃预警", v3.activeAlertCount || 0, "当前范围"], ["商品内容", (window.AppMockData.products || []).length, "模块内容"], ["待办任务", tasks.length, "当前账号"]];
    const modules = [["data-check", "报表"], ["business-products", "商品"], ["business-competitors", "竞品"], ["business-listing", "上新"], ["business-traffic", "流量"], ["business-actions", "待办"], ["feedback-flywheel", "经验回流"], ["business-report", "日志"]];
    return `<section class="owner-hero"><div><p class="eyebrow">AI OPERATING ADVISOR</p><h2>${empty ? "暂无数据" : "经营总览"}</h2><p>首页是产品化封面和经营摘要。导入数据在报表模块完成，模块内容和任务由导入数据生成。</p></div><div class="owner-hero-side"><span>V5</span><strong>数据驱动</strong><small>保留模块，清空托底内容</small></div></section>${empty ? "" : `<section class="kpi-grid owner-metrics">${metrics.map(([label, value, desc]) => AppShell.metricCard(label, value, desc)).join("")}</section>`}<section class="page-section owner-section"><div class="section-header"><div><h3>模块入口</h3><span class="status-badge">原功能保留</span></div></div><div class="owner-module-grid">${modules.map(([route, title]) => card(route, title)).join("")}</div></section><section class="page-section dashboard-queue dashboard-linked-queue"><div class="section-header"><div><h3>当前任务</h3><span class="status-badge">按账号权限</span></div></div>${tasks.length ? tasks.map(taskRow).join("") : `<article class="dashboard-empty">当前没有待处理任务。</article>`}</section>`;
  }
  window.DashboardPage = { route: "dashboard", title: "总览", render() { return renderShell(!hasData()); }, mount(ctx) { ctx.delegate("[data-go]", "click", (_, node) => AppRouter.navigate(node.dataset.go)); ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store"))); } };
})();
