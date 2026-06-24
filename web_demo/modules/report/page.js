(function () {
  const s = (value) => AppShell.escape(value ?? "");
  let lastImportSync = null;

  function latestReport(payload) {
    const groups = payload?.reportGroups || [];
    const first = groups[0] || {};
    const sync = lastImportSync || payload?.v104ImportTaskSync || window.AppApi?.status?.lastImportSync;
    return {
      label: sync?.datasetNames?.join(" / ") || first.name || payload?.v3?.latestDataVersion || "等待导入",
      status: sync?.status === "completed" ? "已更新" : first.status || (payload?.v3?.latestDataVersion ? "已更新" : "待上传"),
      taskCount: sync?.createdTaskCount ?? first.createdTaskCount ?? first.taskCount ?? payload?.recentAlerts?.length ?? 0,
      rows: sync?.rowCount ?? first.rows ?? first.totalRows ?? 0,
      message: sync?.userMessage || sync?.summary,
      modules: sync?.updatedModuleLabels || [],
    };
  }

  function syncStrip(latest) {
    const modules = latest.modules.length ? latest.modules.join(" / ") : "总览 / 经营 / 任务 / 报表 / 日志";
    return `<section class="v102-status-strip v104-import-sync-strip"><strong>${s(latest.status)}</strong><span>${s(latest.message || `已更新，生成 ${latest.taskCount} 个任务`)}</span><span>同步：${s(modules)}</span><button type="button" class="secondary" data-open-tasks>查看任务</button></section>`;
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
      return `<section class="v102-hero report-workbench"><div><h2>上传报表</h2><strong>上传后自动更新经营、任务和日志。</strong></div><div class="v102-primary-action"><button type="button" data-import-mock>上传报表</button><span>${s(latest.message || `已更新 · 生成 ${latest.taskCount} 个任务`)}</span></div></section>
        ${syncStrip(latest)}
        <section class="page-section v102-main-section"><div class="section-header"><h3>最近导入</h3><span class="status-badge">任务驱动</span></div><div class="report-record-list">${groups.length ? groups.map(recordRow).join("") : `<article class="report-record-row"><strong>暂无导入记录</strong><span>上传报表后自动入库</span><span>任务会同步到总览、经营和任务页</span><button type="button" data-import-mock>上传</button></article>`}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-import-mock]", "click", async () => { const result = await AppApi.importMockAlerts(); await AppApi.refreshAfterDataImport(result); lastImportSync = result?.v104ImportTaskSync || window.AppApi?.status?.lastImportSync || null; AppRouter.schedule("v104-import-task-sync"); });
      ctx.delegate("[data-open-tasks]", "click", () => AppRouter.navigate("business-actions"));
      ctx.delegate("[data-report-task]", "click", () => AppRouter.navigate("business-actions"));
      const onSync = (event) => { lastImportSync = event.detail?.sync || lastImportSync; };
      window.addEventListener("v104-import-sync", onSync);
      ctx.addCleanup(() => window.removeEventListener("v104-import-sync", onSync));
    },
  };
})();
