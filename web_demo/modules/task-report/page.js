(function () {
  let lastReport = null;
  let notice = "";
  const s = (value) => AppShell.escape(value);

  function listBlock(title, items = []) {
    return `<section class="page-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${items.length} 项</span></div><div class="report-card-list">${items.map((item) => `<article class="report-card"><p>${s(item)}</p></article>`).join("")}</div></section>`;
  }

  function evidenceBlock(items = []) {
    return `<section class="page-section"><div class="section-header"><h3>数据证据</h3><span class="status-badge">可追溯</span></div><div class="kpi-grid report-metrics">${items.map((item) => `<article class="card report-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`).join("")}</div></section>`;
  }

  function roleInsightBlock(report) {
    const insight = report.roleInsight;
    if (!insight) return "";
    return `<section class="page-section"><div class="section-header"><h3>${s(insight.title)}</h3><span class="status-badge">${s(report.viewer?.roleName || "当前账号")}</span></div><p>${s(insight.summary)}</p><div class="permission-chip-row">${(insight.focus || []).map((item) => `<span>${s(item)}</span>`).join("")}</div>${(insight.hidden || []).length ? `<div class="role-note">已隐藏：${s(insight.hidden.join("、"))}</div>` : ""}</section>`;
  }

  function actionButtons(report) {
    const canCreate = !report.viewer || ["owner", "manager"].includes((report.viewer.insightDepth || "").split("_")[0]) || report.viewer.roleName === "老板账号" || report.viewer.roleName === "店群总管账号";
    if (report.taskId) {
      return `<button type="button" data-back>返回</button><button type="button" data-open-task="${s(report.taskId)}">查看待办任务</button>`;
    }
    const createButton = canCreate ? `<button type="button" class="primary" data-create-task="${s(report.module)}:${s(report.entityId)}">加入任务清单</button>` : "";
    return `<button type="button" data-back>返回</button><button type="button" data-source="${s(report.sourceRoute)}">返回来源模块</button>${createButton}`;
  }

  function renderReport(report) {
    if (!report) return `<section class="page-section"><h3>报告加载失败</h3><p>没有拿到任务报告。请回到来源模块重新打开。</p></section>`;
    const task = report.relatedTask || {};
    return `<section class="report-hero"><div><p class="eyebrow">TASK REPORT · ${s(report.sourceModule)}</p><h2>${s(report.title)}</h2><p>${s(report.warningSummary)}</p></div><div class="report-hero-side"><span>风险等级</span><strong>${s(report.riskLevel)}</strong><small>${s(report.taskStatus || report.reportType)}</small></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid report-metrics">${[["来源模块", report.sourceModule, report.sourceRoute], ["对象 ID", report.entityId, report.module], ["任务状态", report.taskStatus || "候选预警", task.deadline || "待确认"], ["当前视角", report.viewer?.roleName || "默认", report.insightDepth || "role"]].map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section>${roleInsightBlock(report)}${evidenceBlock(report.evidence || [])}<section class="page-section"><div class="section-header"><h3>AI 评估</h3><span class="status-badge">人工确认前</span></div><p>${s(report.aiAssessment)}</p><p>${s(report.agentBoundary)}</p></section>${listBlock("建议动作", report.suggestedActions || [])}${listBlock("运营检查清单", report.operationChecklist || [])}${listBlock("需要补充的数据", report.dataNeeded || [])}${listBlock("人工确认点", report.humanDecision || [])}<section class="page-section"><div class="section-header"><h3>下一步</h3><span class="status-badge">执行建议</span></div><p>${s(report.nextStep)}</p><p>${s(report.archiveRule)}</p><div class="report-actions">${actionButtons(report)}</div></section>`;
  }

  window.TaskReportPage = {
    route: "task-report",
    title: "详情报告",
    async render(ctx) {
      const state = ctx?.state || {};
      if (state.taskId) lastReport = await AppApi.taskReport(state.taskId);
      else if (state.module && state.entityId) lastReport = await AppApi.candidateReport(state.module, state.entityId);
      else lastReport = null;
      return renderReport(lastReport);
    },
    mount(ctx) {
      ctx.delegate("[data-back]", "click", () => {
        const source = lastReport?.taskId ? "business-actions" : lastReport?.sourceRoute;
        AppRouter.navigate(source || "dashboard");
      });
      ctx.delegate("[data-source]", "click", (_, node) => AppRouter.navigate(node.dataset.source || "dashboard"));
      ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask));
      ctx.delegate("[data-create-task]", "click", async (_, node) => {
        const [module, entityId] = node.dataset.createTask.split(":");
        notice = "任务提交中...";
        AppRouter.schedule("task-report-create-start");
        const result = await AppTaskActions.createTaskFromReport(module, entityId);
        const task = result?.task;
        if (task?.id) AppTaskActions.openTodoTask(task.id);
        else {
          notice = result?.message || "任务创建失败，请回到来源模块重试。";
          AppRouter.schedule("task-report-create-failed");
        }
      });
    },
  };
})();
