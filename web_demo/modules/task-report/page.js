(function () {
  let lastReport = null;
  const s = (value) => AppShell.escape(value ?? "");

  function arr(value) { return Array.isArray(value) ? value.filter(Boolean) : []; }
  function task() { return lastReport?.relatedTask || {}; }
  function steps(report) {
    return arr(report?.sopSteps || report?.suggestedActions || report?.operationChecklist || task().sopSteps);
  }
  function evidence(report) {
    return arr(report?.evidence || report?.evidencePack || task().evidencePack || task().evidence).slice(0, 8);
  }
  function renderSteps(report) {
    const list = steps(report);
    if (!list.length) return `<section class="page-section"><div class="section-header"><h3>SOP</h3><span class="status-badge">待补充</span></div><p>当前任务没有返回结构化SOP，请回到任务列表后刷新。</p></section>`;
    return `<section class="page-section action-plan-section"><div class="section-header"><h3>执行SOP</h3><span class="status-badge">${list.length}步</span></div><ol class="action-step-list">${list.map((item) => `<li>${s(item.title || item.action || item.summary || item)}</li>`).join("")}</ol></section>`;
  }
  function renderEvidence(report) {
    const list = evidence(report);
    if (!list.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>证据摘要</h3><span class="status-badge">${list.length}项</span></div><div class="report-card-list compact-report-list">${list.map((item, index) => {
      if (typeof item === "string") return `<article class="report-card compact"><strong>${index + 1}. ${s(item)}</strong></article>`;
      return `<article class="report-card compact"><strong>${s(item.label || item.metric || item.title || `证据 ${index + 1}`)}</strong><p>${s(item.value || item.summary || item.text || item.reason || item.dataVersion || "待确认")}</p></article>`;
    }).join("")}</div></section>`;
  }
  function renderResponsibility(report) {
    const t = report?.relatedTask || {};
    const items = [
      ["店铺", t.store || t.storeName || report?.responsibility?.store?.storeName || "未绑定"],
      ["平台", t.platform || report?.responsibility?.store?.platform || "待确认"],
      ["负责人", t.assigneeName || report?.responsibility?.operatorName || "运营账号"],
      ["复核人", t.reviewerName || report?.responsibility?.reviewerName || "店群总管"],
    ];
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
    const title = report.title || t.title || t.productTitle || "任务详情";
    const reason = report.warningSummary || t.reason || "系统根据报表事实和经营规则生成该任务。";
    return `<section class="report-hero"><div><p class="eyebrow">TASK SOP · V12.10</p><h2>${s(title)}</h2><p>${s(reason)}</p></div><div class="report-hero-side"><span>任务状态</span><strong>${s(report.taskStatus || t.status || "处理中")}</strong><small>${s(report.riskLevel || t.priority || "中")}</small></div></section>${renderSteps(report)}${renderEvidence(report)}${renderResponsibility(report)}<section class="page-section"><div class="section-header"><h3>下一步</h3><span class="status-badge">详情与提交分离</span></div><p>详情页只展示SOP和证据摘要；提交截图、处理说明和数据凭证请进入提交页。</p><div class="report-actions">${actionButtons(report)}</div></section>`;
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
