(function () {
  let lastReport = null;
  let lastAgent = null;
  let notice = "";
  let agentNotice = "";
  const s = (value) => AppShell.escape(value);

  function listBlock(title, items = []) {
    if (!items.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${items.length} 项</span></div><div class="report-card-list">${items.map((item) => `<article class="report-card"><p>${s(item)}</p></article>`).join("")}</div></section>`;
  }

  function evidenceBlock(items = []) {
    if (!items.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>数据证据</h3><span class="status-badge">可追溯</span></div><div class="kpi-grid report-metrics">${items.map((item) => `<article class="card report-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`).join("")}</div></section>`;
  }

  function kvBlock(title, items = []) {
    const list = (items || []).filter((item) => item?.value !== undefined && item?.value !== null && item?.value !== "");
    if (!list.length) return "";
    return `<section class="page-section alert-evidence-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${list.length}</span></div><div class="alert-kv-grid">${list.map((item) => `<article><span>${s(item.label)}</span><strong>${s(item.value)}</strong></article>`).join("")}</div></section>`;
  }

  function triggerBlock(rule) {
    if (!rule) return "";
    return `<section class="page-section alert-evidence-section"><div class="section-header"><h3>触发规则</h3><span class="status-badge">${s(rule.status || "已触发")}</span></div><div class="alert-rule-card"><strong>${s(rule.name || "报表预警")}</strong><p>${s(rule.rule || "命中当前规则阈值后触发。")}</p></div></section>`;
  }

  function responsibilityBlock(info) {
    if (!info?.store) return "";
    const store = info.store;
    return `<section class="page-section alert-evidence-section"><div class="section-header"><h3>责任归属</h3><span class="status-badge">店铺权限</span></div><div class="alert-responsibility-grid"><article><span>责任店铺</span><strong>${s(store.storeName || "未绑定")}</strong></article><article><span>平台</span><strong>${s(store.platform || "待确认")}</strong></article><article><span>负责人</span><strong>${s(info.operatorName || store.operatorName || "待确认")}</strong></article><article><span>复核人</span><strong>${s(info.reviewerName || store.reviewerName || "店群总管")}</strong></article></div></section>`;
  }

  function rawRowsBlock(rows = []) {
    if (!rows.length) return "";
    const headers = Array.from(new Set(rows.flatMap((row) => Object.keys(row || {})))).slice(0, 8);
    return `<section class="page-section alert-evidence-section"><div class="section-header"><h3>原始报表行</h3><span class="status-badge">${rows.length} 行</span></div><div class="report-preview-table"><table><thead><tr>${headers.map((header) => `<th>${s(header)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${headers.map((header) => `<td>${s(row?.[header] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section>`;
  }

  function roleInsightBlock(report) {
    const insight = report.roleInsight;
    if (!insight) return "";
    return `<section class="page-section"><div class="section-header"><h3>${s(insight.title)}</h3><span class="status-badge">${s(report.viewer?.roleName || "当前账号")}</span></div><p>${s(insight.summary)}</p><div class="permission-chip-row">${(insight.focus || []).map((item) => `<span>${s(item)}</span>`).join("")}</div>${(insight.hidden || []).length ? `<div class="role-note">已隐藏：${s(insight.hidden.join("、"))}</div>` : ""}</section>`;
  }

  function agentBlock(agent) {
    if (!agent) return "";
    const drafts = agent.taskDrafts || [];
    const evidence = agent.evidence || [];
    const sourceKey = `${agent.module}:${agent.entityId}`;
    return `<section class="page-section"><div class="section-header"><h3>V4 模块 Agent</h3><span class="status-badge">${s(agent.agentName)}</span></div>${agentNotice ? AppShell.notice("Agent", agentNotice) : ""}<p>${s(agent.summary)}</p><p>${s(agent.boundary)}</p><div class="permission-chip-row">${(agent.forbiddenActions || []).map((item) => `<span>${s(item)}</span>`).join("")}</div><div class="kpi-grid report-metrics">${evidence.slice(0, 4).map((item) => `<article class="card report-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`).join("")}</div>${listBlock("Agent 建议", agent.suggestions || [])}${drafts.length ? `<section class="alert-evidence-section"><div class="section-header"><h3>任务草案</h3><span class="status-badge">人工确认后加入</span></div><div class="report-card-list">${drafts.map((draft, index) => `<article class="report-card"><strong>${s(draft.title || draft.taskType || "任务草案")}</strong><p>${s(draft.task || draft.reason || "待确认")}</p><div class="report-actions"><button type="button" data-agent-task="${s(sourceKey)}:${index}">加入任务清单</button></div></article>`).join("")}</div></section>` : ""}${listBlock("人工确认点", agent.humanDecision || [])}<div class="report-actions"><button type="button" data-refresh-agent>重新生成 Agent 建议</button></div></section>`;
  }

  function actionButtons(report) {
    const canCreate = !report.viewer || ["owner", "manager"].includes((report.viewer.insightDepth || "").split("_")[0]) || report.viewer.roleName === "老板账号" || report.viewer.roleName === "店群总管账号";
    if (report.taskId) {
      return `<button type="button" data-back>返回</button><button type="button" data-open-task="${s(report.taskId)}">查看待办任务</button>`;
    }
    const createButton = canCreate && report.module !== "report-alert" ? `<button type="button" class="primary" data-create-task="${s(report.module)}:${s(report.entityId)}">加入任务清单</button>` : "";
    return `<button type="button" data-back>返回</button><button type="button" data-source="${s(report.sourceRoute)}">返回来源模块</button>${createButton}`;
  }

  async function loadAgentForReport(report) {
    if (!report) return null;
    try {
      if (report.taskId) return await AppApi.moduleAgent("task", report.taskId, "breakdown");
      if (report.module && report.entityId) return await AppApi.moduleAgent(report.module, report.entityId, "analysis");
    } catch (error) {
      console.warn("[task-report] agent load failed", error);
    }
    return null;
  }

  function renderReport(report) {
    if (!report) return `<section class="page-section"><h3>报告加载失败</h3><p>没有拿到任务报告。请回到来源模块重新打开。</p></section>`;
    const task = report.relatedTask || {};
    const metrics = [["来源模块", report.sourceModule, report.sourceRoute], ["对象 ID", report.entityId, report.module], ["任务状态", report.taskStatus || "候选预警", task.deadline || "待确认"], ["当前视角", report.viewer?.roleName || "默认", report.insightDepth || "role"]];
    return `<section class="report-hero"><div><p class="eyebrow">TASK REPORT · ${s(report.sourceModule)}</p><h2>${s(report.title)}</h2><p>${s(report.warningSummary)}</p></div><div class="report-hero-side"><span>风险等级</span><strong>${s(report.riskLevel)}</strong><small>${s(report.taskStatus || report.reportType)}</small></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid report-metrics">${metrics.map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section>${roleInsightBlock(report)}${kvBlock("来源链路", report.sourceTrace || [])}${triggerBlock(report.triggerRule)}${responsibilityBlock(report.responsibility)}${evidenceBlock(report.evidence || [])}${rawRowsBlock(report.rawRows || [])}${listBlock("证据链", report.evidenceChain || [])}<section class="page-section"><div class="section-header"><h3>AI 评估</h3><span class="status-badge">人工确认前</span></div><p>${s(report.aiAssessment)}</p><p>${s(report.agentBoundary)}</p></section>${agentBlock(lastAgent)}${listBlock("建议动作", report.suggestedActions || [])}${listBlock("运营检查清单", report.operationChecklist || [])}${listBlock("需要补充的数据", report.dataNeeded || [])}${listBlock("人工确认点", report.humanDecision || [])}<section class="page-section"><div class="section-header"><h3>下一步</h3><span class="status-badge">执行建议</span></div><p>${s(report.nextStep)}</p><p>${s(report.archiveRule)}</p><div class="report-actions">${actionButtons(report)}</div></section>`;
  }

  window.TaskReportPage = {
    route: "task-report",
    title: "详情报告",
    async render(ctx) {
      const state = ctx?.state || {};
      lastAgent = null;
      if (state.alertId) lastReport = await AppApi.alertReport(state.alertId);
      else if (state.taskId) lastReport = await AppApi.taskReport(state.taskId);
      else if (state.module && state.entityId) lastReport = await AppApi.candidateReport(state.module, state.entityId);
      else lastReport = null;
      lastAgent = await loadAgentForReport(lastReport);
      return renderReport(lastReport);
    },
    mount(ctx) {
      ctx.delegate("[data-back]", "click", () => {
        const source = lastReport?.taskId ? "business-actions" : lastReport?.sourceRoute;
        AppRouter.navigate(source || "dashboard");
      });
      ctx.delegate("[data-source]", "click", (_, node) => AppRouter.navigate(node.dataset.source || "dashboard"));
      ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask));
      ctx.delegate("[data-refresh-agent]", "click", async () => {
        agentNotice = "Agent 重新生成中...";
        AppRouter.schedule("task-report-agent-refresh-start");
        lastAgent = await loadAgentForReport(lastReport);
        agentNotice = lastAgent ? "Agent 建议已更新，仍需人工确认后执行。" : "Agent 暂时没有生成结果。";
        AppRouter.schedule("task-report-agent-refresh-done");
      });
      ctx.delegate("[data-agent-task]", "click", async (_, node) => {
        const parts = (node.dataset.agentTask || "").split(":");
        const module = parts[0];
        const entityId = parts[1];
        const draftIndex = Number(parts[2] || 0);
        agentNotice = "Agent 任务草案提交中...";
        AppRouter.schedule("task-report-agent-task-start");
        const result = await AppApi.createAgentTask(module, entityId, draftIndex, lastAgent?.mode || "analysis");
        const task = result?.task;
        if (task?.id) AppTaskActions.openTodoTask(task.id);
        else {
          agentNotice = result?.message || "Agent 任务草案创建失败，请回到来源模块重试。";
          AppRouter.schedule("task-report-agent-task-failed");
        }
      });
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
