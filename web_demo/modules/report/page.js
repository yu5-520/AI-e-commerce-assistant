(function () {
  let detailId = null;
  let notice = "";
  const s = (value) => AppShell.escape(value);
  function v3() { return AppMockData.v3 || { activeAlertCount: 0, highPriorityAlertCount: 0, taskLinkedAlertCount: 0, latestAlerts: [] }; }
  function taskButton(report) {
    const task = AppTaskActions.findOpenTask(report);
    return task ? `<button type="button" data-open-task="${s(task.id)}" class="ghost">已在任务清单</button><button type="button" data-task-report="${s(task.id)}">任务报告</button>` : `<button type="button" data-candidate-report="report:${s(report.id)}">查看预警</button><button type="button" data-task="${s(report.id)}">导入复盘</button>`;
  }
  function alertBadge(report) {
    const count = report.dataRefreshState?.activeAlertCount || 0;
    return count ? `<span class="status-badge danger">${s(count)} 个预警</span>` : `<span class="status-badge">待导入</span>`;
  }
  function card(report) { return `<article class="report-card"><div><h3>${s(report.name)}</h3><p>${s(report.desc)}</p><div class="report-meta"><span>${s(report.source)}</span><span>${s(report.status)}</span><span>${s(report.count)}</span>${alertBadge(report)}</div></div><div class="report-actions"><button type="button" data-detail="${s(report.id)}">查看报表</button>${taskButton(report)}</div></article>`; }
  function detail(report) { const card = AppMockData.reportGroups.flatMap((group) => group.reports).find((item) => item.id === detailId) || { id: detailId }; return `<section class="report-detail-hero"><div><p class="eyebrow">${s(report.source)} REPORT</p><h2>${s(report.title)}</h2><p>从报表明细进入真实经营判断，避免只看系统状态。</p></div><div class="report-actions"><button type="button" data-back>返回报表管理</button>${taskButton(card)}</div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid report-metrics">${report.summary.map(([label, value]) => `<article class="card report-metric-card"><h3>${s(label)}</h3><strong>${s(value)}</strong></article>`).join("")}</section><section class="page-section report-table-section"><div class="section-header"><h3>报表明细</h3><span class="status-badge">接口数据</span></div>${AppShell.table(report.columns, report.rows)}</section>`; }
  function v3Metrics() {
    const data = v3();
    return [["新增预警", data.activeAlertCount || 0, "报表触发"], ["高风险", data.highPriorityAlertCount || 0, "优先处理"], ["已进待办", data.taskLinkedAlertCount || 0, "任务同步"], ["最近版本", data.latestDataVersion || "未导入", data.latestDatasetName || "等待报表"]].map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("");
  }
  window.ReportPage = {
    route: "data-check",
    title: "报表",
    render() {
      if (detailId && AppMockData.reportDetails[detailId]) return detail(AppMockData.reportDetails[detailId]);
      return `<section class="report-hero"><div><p class="eyebrow">REPORT CENTER · V3.0</p><h2>ERP / CRM 报表管理</h2><p>上传或导入新报表后，系统会生成数据版本、识别异常、同步首页、商品页、流量页和待办。</p></div><div class="report-hero-side"><span>数据更新</span><strong>报表触发预警</strong><small>${s(v3().latestSnapshotAt || "等待导入")}</small><button type="button" data-v3-import>一键生成预警</button></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid report-metrics">${v3Metrics()}</section>${(v3().latestAlerts || []).length ? `<section class="page-section report-section"><div class="section-header"><h3>最新预警</h3><span class="status-badge">${s((v3().latestAlerts || []).length)} 条</span></div><div class="report-card-list">${v3().latestAlerts.map((alert) => `<article class="report-card"><div><h3>${s(alert.alertType)}</h3><p>${s(alert.entityId)} · ${s(alert.riskDomain)} · ${s(alert.priority)}</p><div class="report-meta"><span>${s(alert.sourceDataset)}</span><span>${s(alert.dataVersion)}</span><span>${s(alert.status)}</span></div></div><div class="report-actions">${alert.taskId ? `<button type="button" data-open-task="${s(alert.taskId)}">查看待办</button>` : ""}</div></article>`).join("")}</div></section>` : ""}${AppMockData.reportGroups.map((group) => `<section class="page-section report-section"><div class="section-header"><h3>${s(group.title)}</h3><span class="status-badge">可查看</span></div><div class="report-card-list">${group.reports.map(card).join("")}</div></section>`).join("")}`;
    },
    mount(ctx) {
      ctx.delegate("[data-v3-import]", "click", async () => { notice = "正在导入报表并生成预警..."; AppRouter.schedule("v3-import-start"); const result = await AppApi.importMockAlerts(); await AppApi.refreshAfterDataImport(); notice = result?.alertCount || result?.createdTaskCount ? `已生成 ${result.alertCount || 0} 条预警，${result.createdTaskCount || 0} 条进入待办。` : "报表已检查，暂无新增预警。"; AppRouter.schedule("v3-import-done"); });
      ctx.delegate("[data-detail]", "click", (_, node) => { detailId = node.dataset.detail; notice = ""; AppRouter.schedule("report-detail"); });
      ctx.delegate("[data-back]", "click", () => { detailId = null; notice = ""; AppRouter.schedule("report-back"); });
      ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask));
      ctx.delegate("[data-task-report]", "click", (_, node) => AppTaskActions.openTaskReport(node.dataset.taskReport));
      ctx.delegate("[data-candidate-report]", "click", (_, node) => { const [module, id] = node.dataset.candidateReport.split(":"); AppTaskActions.openCandidateReport(module, id); });
      ctx.delegate("[data-task]", "click", async (_, node) => { notice = "任务提交中..."; AppRouter.schedule("report-task-start"); const result = await AppTaskActions.createReportTask(node.dataset.task); notice = result?.message || "报表任务已处理。"; AppRouter.schedule("report-task"); });
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();
