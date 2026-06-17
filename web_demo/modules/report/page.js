(function () {
  let detailId = null;
  let notice = "";
  let selectedDataset = "inventory";
  let selectedFileName = "";
  const s = (value) => AppShell.escape(value);
  const datasetOptions = [
    ["inventory", "库存报表"],
    ["refunds", "退款报表"],
    ["orders", "订单报表"],
    ["products", "商品报表"],
    ["customers", "客户报表"],
  ];
  function v3() { return AppMockData.v3 || { activeAlertCount: 0, highPriorityAlertCount: 0, taskLinkedAlertCount: 0, latestAlerts: [] }; }
  function shortVersion(value) { const text = String(value || "未导入"); return text.length > 22 ? `${text.slice(0, 22)}...` : text; }
  function taskButton(report) {
    const task = AppTaskActions.findOpenTask(report);
    return task ? `<button type="button" data-open-task="${s(task.id)}" class="ghost">已在任务清单</button><button type="button" data-task-report="${s(task.id)}">任务报告</button>` : `<button type="button" data-candidate-report="report:${s(report.id)}">查看预警</button><button type="button" data-task="${s(report.id)}">导入复盘</button>`;
  }
  function alertBadge(report) {
    const count = report.dataRefreshState?.activeAlertCount || 0;
    return count ? `<span class="status-badge danger">${s(count)} 个预警</span>` : `<span class="status-badge">待导入</span>`;
  }
  function parseCsv(text) {
    const rows = [];
    let row = [];
    let cell = "";
    let quoted = false;
    const source = String(text || "").replace(/^\uFEFF/, "");
    for (let index = 0; index < source.length; index += 1) {
      const char = source[index];
      const next = source[index + 1];
      if (char === '"' && quoted && next === '"') { cell += '"'; index += 1; continue; }
      if (char === '"') { quoted = !quoted; continue; }
      if (char === "," && !quoted) { row.push(cell.trim()); cell = ""; continue; }
      if ((char === "\n" || char === "\r") && !quoted) {
        if (char === "\r" && next === "\n") index += 1;
        row.push(cell.trim());
        if (row.some((item) => item !== "")) rows.push(row);
        row = [];
        cell = "";
        continue;
      }
      cell += char;
    }
    row.push(cell.trim());
    if (row.some((item) => item !== "")) rows.push(row);
    if (rows.length < 2) return [];
    const headers = rows[0].map((item) => item.trim());
    return rows.slice(1).map((values) => Object.fromEntries(headers.map((key, index) => [key, values[index] ?? ""]))).filter((item) => Object.values(item).some((value) => String(value || "").trim()));
  }
  function card(report) { return `<article class="report-card"><div><h3>${s(report.name)}</h3><p>${s(report.desc)}</p><div class="report-meta"><span>${s(report.source)}</span><span>${s(report.status)}</span><span>${s(report.count)}</span>${alertBadge(report)}</div></div><div class="report-actions"><button type="button" data-detail="${s(report.id)}">查看报表</button>${taskButton(report)}</div></article>`; }
  function detail(report) { const card = AppMockData.reportGroups.flatMap((group) => group.reports).find((item) => item.id === detailId) || { id: detailId }; return `<section class="report-detail-hero"><div><p class="eyebrow">${s(report.source)} REPORT</p><h2>${s(report.title)}</h2><p>从报表明细进入真实经营判断，避免只看系统状态。</p></div><div class="report-actions"><button type="button" data-back>返回报表管理</button>${taskButton(card)}</div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid report-metrics">${report.summary.map(([label, value]) => `<article class="card report-metric-card"><h3>${s(label)}</h3><strong>${s(value)}</strong></article>`).join("")}</section><section class="page-section report-table-section"><div class="section-header"><h3>报表明细</h3><span class="status-badge">接口数据</span></div>${AppShell.table(report.columns, report.rows)}</section>`; }
  function uploadCard() {
    return `<div class="report-upload-card"><div><span>主流程</span><strong>上传报表</strong><small>上传后自动检查并生成预警</small></div><label class="report-upload-field"><span>报表类型</span><select data-report-type>${datasetOptions.map(([value, label]) => `<option value="${s(value)}" ${value === selectedDataset ? "selected" : ""}>${s(label)}</option>`).join("")}</select></label><button type="button" data-upload-report>选择文件并导入</button><input id="reportFileInput" type="file" accept=".csv,text/csv" data-report-file hidden /><small class="report-upload-tip">${s(selectedFileName || "支持 CSV。导入完成后自动同步首页、商品、流量和待办。")}</small><button type="button" class="ghost" data-v3-demo>备用：使用示例数据试跑</button></div>`;
  }
  function v3Metrics() {
    const data = v3();
    return [["新增预警", data.activeAlertCount || 0, "报表触发"], ["高风险", data.highPriorityAlertCount || 0, "优先处理"], ["已进待办", data.taskLinkedAlertCount || 0, "任务同步"], ["最近版本", shortVersion(data.latestDataVersion), data.latestDatasetName || "等待报表"]].map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("");
  }
  async function importSelectedFile(file) {
    if (!file) { notice = "请选择要导入的 CSV 报表。"; AppRouter.schedule("report-upload-empty"); return; }
    selectedFileName = file.name;
    notice = `正在导入${file.name}，系统会自动检查并生成预警...`;
    AppRouter.schedule("report-upload-start");
    const text = await file.text();
    const rows = parseCsv(text);
    if (!rows.length) {
      notice = "文件没有读取到有效数据。请确认第一行为字段名，下面是报表数据。";
      AppRouter.schedule("report-upload-invalid");
      return;
    }
    const result = await AppApi.importReportRows(selectedDataset, rows);
    await AppApi.refreshAfterDataImport();
    notice = `导入完成：${result?.datasetName || selectedDataset} 生成 ${result?.alertCount || 0} 条预警，${result?.createdTaskCount || 0} 条已进入待办，相关模块已同步。`;
    AppRouter.schedule("report-upload-done");
  }
  window.ReportPage = {
    route: "data-check",
    title: "报表",
    render() {
      if (detailId && AppMockData.reportDetails[detailId]) return detail(AppMockData.reportDetails[detailId]);
      return `<section class="report-hero"><div><p class="eyebrow">REPORT CENTER · V3.0.1</p><h2>ERP / CRM 报表管理</h2><p>上传订单、退款、库存、商品报表后，系统会自动生成数据版本、识别异常、同步首页、商品页、流量页和待办。</p></div>${uploadCard()}</section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid report-metrics">${v3Metrics()}</section>${(v3().latestAlerts || []).length ? `<section class="page-section report-section"><div class="section-header"><h3>最新预警</h3><span class="status-badge">${s((v3().latestAlerts || []).length)} 条</span></div><div class="report-card-list">${v3().latestAlerts.map((alert) => `<article class="report-card"><div><h3>${s(alert.alertType)}</h3><p>${s(alert.entityId)} · ${s(alert.riskDomain)} · ${s(alert.priority)}</p><div class="report-meta"><span>${s(alert.sourceDataset)}</span><span title="${s(alert.dataVersion)}">${s(shortVersion(alert.dataVersion))}</span><span>${s(alert.status)}</span></div></div><div class="report-actions">${alert.taskId ? `<button type="button" data-open-task="${s(alert.taskId)}">查看待办</button>` : ""}</div></article>`).join("")}</div></section>` : ""}${AppMockData.reportGroups.map((group) => `<section class="page-section report-section"><div class="section-header"><h3>${s(group.title)}</h3><span class="status-badge">可查看</span></div><div class="report-card-list">${group.reports.map(card).join("")}</div></section>`).join("")}`;
    },
    mount(ctx) {
      ctx.delegate("[data-report-type]", "change", (_, node) => { selectedDataset = node.value || "inventory"; });
      ctx.delegate("[data-upload-report]", "click", () => document.getElementById("reportFileInput")?.click());
      ctx.delegate("[data-report-file]", "change", async (_, node) => { await importSelectedFile(node.files?.[0]); node.value = ""; });
      ctx.delegate("[data-v3-demo]", "click", async () => { notice = "正在使用示例报表试跑预警链路..."; AppRouter.schedule("v3-demo-start"); const result = await AppApi.importMockAlerts(); await AppApi.refreshAfterDataImport(); notice = result?.alertCount || result?.createdTaskCount ? `示例数据已生成 ${result.alertCount || 0} 条预警，${result.createdTaskCount || 0} 条进入待办。` : "示例报表已检查，暂无新增预警。"; AppRouter.schedule("v3-demo-done"); });
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
