(function () {
  let lastReport = null;
  const s = (value) => AppShell.escape(value ?? "");

  function arr(value) { return Array.isArray(value) ? value.filter(Boolean) : []; }
  function task() { return lastReport?.relatedTask || {}; }
  function steps(report) { return arr(report?.operatorSopSteps || report?.sopSteps || report?.suggestedActions || report?.operationChecklist || task().sopSteps); }
  function changePack(report) { return report?.systemChangePack || task().systemChangePack || {}; }
  function agent(report) { return report?.agentOperatingJudgment || task().agentOperatingJudgment || {}; }
  function recapLine(report) { return arr(report?.systemRecapLine || task().systemRecapLine || agent(report).systemRecapLine); }
  function evidence(report) {
    const packLines = arr(changePack(report).lines);
    if (packLines.length) return packLines.slice(0, 12);
    return arr(report?.evidence || report?.evidencePack || task().evidencePack || task().evidence).slice(0, 10);
  }
  function renderChangePack(report) {
    const list = evidence(report);
    if (!list.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>系统拆分的数据变化</h3><span class="status-badge">交叉验证链</span></div><div class="report-card-list compact-report-list">${list.map((item, index) => {
      if (typeof item === "string") return `<article class="report-card compact"><strong>${index + 1}. ${s(item)}</strong></article>`;
      return `<article class="report-card compact"><strong>${s(item.role || item.label || item.metricName || item.title || `变化 ${index + 1}`)}</strong><p>${s(item.summary || item.reason || item.value || item.text || item.dataVersion || "待确认")}</p></article>`;
    }).join("")}</div></section>`;
  }
  function renderAgentJudgment(report) {
    const info = agent(report);
    const judgment = info.judgment || report?.warningSummary || task().reason;
    if (!judgment) return "";
    const tags = [info.roiChange && `ROI ${info.roiChange}`, info.gmvChange && `GMV ${info.gmvChange}`, info.adSpendChange && `广告 ${info.adSpendChange}`, info.clickChange && `点击 ${info.clickChange}`, info.conversionChange && `转化 ${info.conversionChange}`].filter(Boolean);
    return `<section class="page-section"><div class="section-header"><h3>Agent经营判断</h3><span class="status-badge">基于变化包生成</span></div><div class="agent-judgment-card"><strong>${s(info.title || "经营判断")}</strong><p>${s(judgment)}</p>${tags.length ? `<div class="todo-compact-tags">${tags.map((item) => `<em>${s(item)}</em>`).join("")}</div>` : ""}</div></section>`;
  }
  function renderSteps(report) {
    const list = steps(report);
    if (!list.length) return `<section class="page-section"><div class="section-header"><h3>Agent执行SOP</h3><span class="status-badge">待补充</span></div><p>当前任务没有返回结构化SOP，请回到任务列表后刷新。</p></section>`;
    return `<section class="page-section action-plan-section"><div class="section-header"><h3>Agent执行SOP</h3><span class="status-badge">运营只执行</span></div><ol class="action-step-list">${list.map((item) => `<li>${s(item.title || item.action || item.summary || item)}</li>`).join("")}</ol></section>`;
  }
  function renderAutoRecap(report) {
    const list = recapLine(report);
    if (!list.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>系统自动复盘线</h3><span class="status-badge">运营无需复盘</span></div><ol class="action-step-list recap-line-list">${list.map((item) => `<li>${s(item)}</li>`).join("")}</ol></section>`;
  }
  function renderDataGaps(report) {
    const gaps = arr(changePack(report).dataGaps);
    if (!gaps.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>数据缺口</h3><span class="status-badge">不生成伪动作</span></div><div class="report-card-list compact-report-list">${gaps.map((item) => `<article class="report-card compact"><strong>${s(item.field || "数据缺口")}</strong><p>${s(item.impact || item.status || "当前不生成对应动作")}</p></article>`).join("")}</div></section>`;
  }
  function renderResponsibility(report) {
    const t = report?.relatedTask || {};
    const items = [["店铺", t.store || t.storeName || report?.responsibility?.store?.storeName || "未绑定"], ["平台", t.platform || report?.responsibility?.store?.platform || "待确认"], ["负责人", t.assigneeName || report?.responsibility?.operatorName || "运营账号"], ["复核人", t.reviewerName || report?.responsibility?.reviewerName || "店群总管"]];
    return `<section class="page-section"><div class="section-header"><h3>责任与状态</h3><span class="status-badge">${s(report?.taskStatus || t.status || "任务")}</span></div><div class="alert-kv-grid">${items.map(([label, value]) => `<article><span>${s(label)}</span><strong>${s(value)}</strong></article>`).join("")}</div></section>`;
  }
  function actionButtons(report) {
    const id = report?.taskId || task().id;
    const submit = id && ["处理中", "已退回"].includes(String(report?.taskStatus || task().status || "")) ? `<button type="button" data-open-submit="${s(id)}">去提交材料</button>` : "";
    return `${submit}<button type="button" class="secondary" data-back>返回任务列表</button>`;
  }
  function renderReport(report) {
    if (!report) return `<section class="page-section"><h3>详情加载失败</h3><p>没有拿到任务详情。请回到任务列表重新打开。</p><button data-back>返回任务列表</button></section>`;
    const t = report.relatedTask || {};
    const info = agent(report);
    const title = report.title || t.title || info.title || t.productTitle || "任务详情";
    const reason = report.warningSummary || info.judgment || t.reason || "系统已拆分数据变化，Agent生成执行SOP。";
    return `<section class="report-hero"><div><p class="eyebrow">TASK SOP · V12.11</p><h2>${s(title)}</h2><p>${s(reason)}</p></div><div class="report-hero-side"><span>任务状态</span><strong>${s(report.taskStatus || t.status || "处理中")}</strong><small>系统拆数据 · Agent生成SOP</small></div></section>${renderChangePack(report)}${renderAgentJudgment(report)}${renderSteps(report)}${renderAutoRecap(report)}${renderDataGaps(report)}${renderResponsibility(report)}<section class="page-section"><div class="section-header"><h3>下一步</h3><span class="status-badge">提交后系统复盘</span></div><p>运营只执行Agent SOP并提交材料；后续报表或接口数据更新后，系统自动复盘并写入日报、周报和复盘库。</p><div class="report-actions">${actionButtons(report)}</div></section>`;
  }

  window.TaskReportPage = {
    route: "task-report",
    title: "任务详情",
    async render(ctx) {
      const state = ctx?.state || {};
      if (state.alertId) lastReport = await AppApi.alertReport(state.alertId);
      else if (state.taskId) lastReport = await AppApi.taskReport(state.taskId);
      else if (state.module && state.entityId) lastReport = await AppApi.candidateReport(state.module, state.entityId);
      else lastReport = lastReport || null;
      return renderReport(lastReport);
    },
    mount(ctx) {
      ctx.delegate("[data-back]", "click", () => AppRouter.navigate("business-actions", lastReport?.taskId ? { focusTaskId: lastReport.taskId } : null));
      ctx.delegate("[data-open-submit]", "click", (_, node) => AppRouter.navigate("task-submit", { taskId: node.dataset.openSubmit }));
    },
  };
})();
