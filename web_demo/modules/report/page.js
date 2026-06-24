(function () {
  const s = (value) => AppShell.escape(value ?? "");

  function latestReport(payload) {
    const groups = payload?.reportGroups || [];
    const first = groups[0] || {};
    return {
      label: first.name || payload?.v3?.latestDataVersion || "等待导入",
      status: first.status || (payload?.v3?.latestDataVersion ? "已更新" : "待上传"),
      taskCount: first.createdTaskCount ?? first.taskCount ?? payload?.recentAlerts?.length ?? 0,
      rows: first.rows ?? first.totalRows ?? 0,
    };
  }

  function recordRow(item) {
    return `<article class="report-record-row"><strong>${s(item.name || item.label || "报表记录")}</strong><span>${s(item.status || "已处理")}</span><span>生成 ${s(item.createdTaskCount ?? item.taskCount ?? 0)} 个任务</span><button type="button" data-report-task="${s(item.id || item.name || "report")}">查看任务</button></article>`;
  }

  window.ReportPage = {
    route: "data-check",
    title: "报表",
    async render() {
      const payload = await AppApi.report();
      const latest = latestReport(payload || {});
      const groups = payload?.reportGroups || [];
      return `<section class="v102-hero report-workbench"><div><h2>上传报表</h2><strong>系统会自动更新经营数据并生成任务。</strong></div><div class="v102-primary-action"><button type="button" data-import-mock>上传报表</button><span>已更新 · 生成 ${s(latest.taskCount)} 个任务</span></div></section>
        <section class="v102-status-strip"><strong>${s(latest.status)}</strong><span>${s(latest.label)}</span><span>${s(latest.rows)} 条记录</span><button type="button" class="secondary" data-open-tasks>查看任务</button></section>
        <section class="page-section v102-main-section"><div class="section-header"><h3>最近导入</h3><span class="status-badge">同步结果</span></div><div class="report-record-list">${groups.length ? groups.map(recordRow).join("") : `<article class="report-record-row"><strong>暂无导入记录</strong><span>上传报表后自动入库</span><span>任务会同步到总览和任务页</span><button type="button" data-import-mock>上传</button></article>`}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-import-mock]", "click", async () => { await AppApi.importMockAlerts(); await AppApi.refreshAfterDataImport(); AppRouter.schedule("report-imported"); });
      ctx.delegate("[data-open-tasks]", "click", () => AppRouter.navigate("business-actions"));
      ctx.delegate("[data-report-task]", "click", () => AppRouter.navigate("business-actions"));
    },
  };
})();
