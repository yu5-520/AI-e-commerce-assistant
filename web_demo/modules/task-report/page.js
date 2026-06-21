(function () {
  let lastReport = null;
  let lastAgent = null;
  let notice = "";
  let agentNotice = "";
  const s = (value) => AppShell.escape(value ?? "");

  function listBlock(title, items = [], options = {}) {
    const list = (items || []).filter(Boolean);
    if (!list.length) return "";
    const label = options.label || `${list.length} 项`;
    return `<section class="page-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${s(label)}</span></div><div class="report-card-list">${list.map((item, index) => {
      if (typeof item === "string") return `<article class="report-card"><strong>${index + 1}. ${s(item)}</strong></article>`;
      return `<article class="report-card"><strong>${s(item.title || item.label || `第 ${index + 1} 项`)}</strong><p>${s(item.value || item.summary || item.text || item.reason || "待确认")}</p></article>`;
    }).join("")}</div></section>`;
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

  function isCreativeSignal(report) {
    const task = report?.relatedTask || {};
    const text = [report?.title, report?.warningSummary, task?.title, task?.task, task?.riskDomain, task?.taskType, ...(task?.judgmentTags || [])].filter(Boolean).join(" ");
    return /点击|CTR|主图|标题|创意|转化/.test(text) && (task.productId || report?.entityId);
  }

  function packageCard(pkg, index, productId) {
    return `<article class="report-card"><header><strong>${s(pkg.packageName || `方案 ${index + 1}`)}</strong><span class="status-badge">${s(pkg.targetMetric || "点击率")}</span></header>
      <p><b>标题：</b>${s(pkg.title)}</p>
      <p><b>主图：</b>${s(pkg.mainImageDirection)} · ${s(pkg.mainImageLayout)}</p>
      <p><b>首图文案：</b>${s(pkg.firstImageText)}</p>
      <p><b>卖点顺序：</b>${s((pkg.sellingPointOrder || []).join(" → "))}</p>
      <div class="permission-chip-row"><span>${s(pkg.fitPlatform || "通用")}</span><span>${s(pkg.fitTraffic || "测试流量")}</span><span>${s(pkg.testDuration || "24-48 小时")}</span></div>
      <p><b>运营执行：</b>${s((pkg.operatorAction || []).join("；"))}</p>
      <p><b>提交指标：</b>${s((pkg.submitMetrics || []).join("、"))}</p>
      <p><b>风险：</b>${s(pkg.risk || "避免夸大承诺")}</p>
      <div class="report-actions"><button type="button" data-creative-task="${s(productId)}:${index}">选择此方案创建测试任务</button></div>
    </article>`;
  }

  function testPackagesBlock(agent) {
    const packages = agent?.testPackages || [];
    if (!packages.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>Agent 测试包</h3><span class="status-badge">运营直接上架测试</span></div><div class="report-card-list">${packages.map((pkg, index) => packageCard(pkg, index, agent.productId || lastReport?.relatedTask?.productId || lastReport?.entityId)).join("")}</div></section>`;
  }

  function actionPlanBlock(agent, report) {
    if (agent?.testPackages?.length) return testPackagesBlock(agent);
    const suggestions = (agent?.structuredSteps || agent?.suggestions || report?.suggestedActions || []).filter(Boolean);
    if (!suggestions.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>Agent 处理方案</h3><span class="status-badge">转成运营动作</span></div><div class="report-card-list">${suggestions.map((item, index) => `<article class="report-card"><strong>${index + 1}. ${s(item.title || item)}</strong>${item.summary || item.action ? `<p>${s(item.summary || item.action)}</p>` : ""}</article>`).join("")}</div></section>`;
  }

  function taskDraftCard(draft, index, sourceKey) {
    const steps = draft.executionSteps || [];
    const evidence = draft.evidenceRequired || [];
    const criteria = draft.acceptanceCriteria || [];
    return `<article class="report-card"><header><strong>${s(draft.title || draft.taskType || "任务草案")}</strong><span class="status-badge">${s(draft.priority || "待确认")}</span></header><p>${s(draft.task || draft.reason || "待确认")}</p>${steps.length ? `<p><b>执行动作：</b>${s(steps.join("；"))}</p>` : ""}${evidence.length ? `<p><b>提交证据：</b>${s(evidence.join("、"))}</p>` : ""}${criteria.length ? `<p><b>复核标准：</b>${s(criteria.join("、"))}</p>` : ""}<div class="report-actions"><button type="button" data-agent-task="${s(sourceKey)}:${index}">确认加入任务清单</button></div></article>`;
  }

  function taskDraftBlock(agent) {
    const drafts = agent?.taskDrafts || (agent?.taskDraft ? [agent.taskDraft] : []);
    if (!drafts.length) return "";
    const sourceKey = `${agent.module || "creative"}:${agent.entityId || agent.productId || lastReport?.entityId}`;
    return `<section class="page-section"><div class="section-header"><h3>任务草案</h3><span class="status-badge">人工确认后加入</span></div><div class="report-card-list">${drafts.map((draft, index) => taskDraftCard(draft, index, sourceKey)).join("")}</div></section>`;
  }

  function agentBlock(agent, report) {
    if (!agent) return "";
    const evidence = agent.evidence || [];
    return `${agentNotice ? AppShell.notice("Agent", agentNotice) : ""}<section class="page-section"><div class="section-header"><h3>Agent 判断</h3><span class="status-badge">${s(agent.agentName || "Agent")}</span></div><p>${s(agent.categoryStrategy || agent.summary || "已生成处理方案。")}</p>${evidence.length ? `<div class="kpi-grid report-metrics">${evidence.slice(0, 4).map((item) => `<article class="card report-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`).join("")}</div>` : ""}</section>${actionPlanBlock(agent, report)}${taskDraftBlock(agent)}<section class="page-section"><div class="section-header"><h3>人工确认</h3><span class="status-badge">${s((agent.humanDecision || report.humanDecision || []).length)} 项</span></div><div class="report-card-list">${(agent.humanDecision || report.humanDecision || []).map((item) => `<article class="report-card"><strong>${s(item)}</strong></article>`).join("")}</div><div class="report-actions"><button type="button" data-refresh-agent>重新生成 Agent 方案</button></div></section>`;
  }

  function actionButtons(report) {
    const canCreate = !report.viewer || ["owner", "manager"].includes((report.viewer.insightDepth || "").split("_")[0]) || report.viewer.roleName === "老板账号" || report.viewer.roleName === "店群总管账号";
    if (report.taskId) return `<button type="button" data-back>返回</button><button type="button" data-open-task="${s(report.taskId)}">查看待办任务</button>`;
    const createButton = canCreate && report.module !== "report-alert" ? `<button type="button" class="primary" data-create-task="${s(report.module)}:${s(report.entityId)}">加入任务清单</button>` : "";
    return `<button type="button" data-back>返回</button><button type="button" data-source="${s(report.sourceRoute)}">返回来源模块</button>${createButton}`;
  }

  async function loadAgentForReport(report) {
    if (!report) return null;
    try {
      const task = report.relatedTask || {};
      if (isCreativeSignal(report) && (task.productId || report.entityId)) {
        return await AppApi.creativeAgent(task.productId || report.entityId, {
          taskGoal: report.warningSummary || task.task || "提升点击率和转化率",
          platform: task.platform || "通用",
          categoryId: task.categoryId || "home_living_goods",
        });
      }
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
    return `<section class="report-hero"><div><p class="eyebrow">TASK REPORT · ${s(report.sourceModule)}</p><h2>${s(report.title)}</h2><p>${s(report.warningSummary)}</p></div><div class="report-hero-side"><span>风险等级</span><strong>${s(report.riskLevel)}</strong><small>${s(report.taskStatus || report.reportType)}</small></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid report-metrics">${metrics.map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section>${kvBlock("来源链路", report.sourceTrace || [])}${triggerBlock(report.triggerRule)}${responsibilityBlock(report.responsibility)}${evidenceBlock(report.evidence || [])}${rawRowsBlock(report.rawRows || [])}${listBlock("证据链", report.evidenceChain || [])}${agentBlock(lastAgent, report)}${listBlock("需要补充的数据", report.dataNeeded || [])}<section class="page-section"><div class="section-header"><h3>下一步</h3><span class="status-badge">人工确认</span></div><p>${s(report.nextStep)}</p><div class="report-actions">${actionButtons(report)}</div></section>`;
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
        agentNotice = "Agent 方案重新生成中...";
        AppRouter.schedule("task-report-agent-refresh-start");
        lastAgent = await loadAgentForReport(lastReport);
        agentNotice = lastAgent ? "Agent 方案已更新，仍需人工确认后执行。" : "Agent 暂时没有生成结果。";
        AppRouter.schedule("task-report-agent-refresh-done");
      });
      ctx.delegate("[data-creative-task]", "click", async (_, node) => {
        const [productId, packageIndex] = (node.dataset.creativeTask || "").split(":");
        agentNotice = "测试任务创建中...";
        AppRouter.schedule("task-report-creative-task-start");
        const result = await AppApi.createCreativeTask(productId, { packageIndex: Number(packageIndex || 0), taskGoal: lastAgent?.taskGoal, platform: lastAgent?.platformRule?.platform || lastAgent?.productFacts?.platform || "通用", categoryId: lastAgent?.categoryProfile?.categoryId || "home_living_goods" });
        const task = result?.task;
        if (task?.id) AppTaskActions.openTodoTask(task.id);
        else {
          agentNotice = result?.message || "测试任务创建失败，请回到商品模块重试。";
          AppRouter.schedule("task-report-creative-task-failed");
        }
      });
      ctx.delegate("[data-agent-task]", "click", async (_, node) => {
        const parts = (node.dataset.agentTask || "").split(":");
        const module = parts[0];
        const entityId = parts[1];
        const draftIndex = Number(parts[2] || 0);
        if (module === "creative") {
          const result = await AppApi.createCreativeTask(entityId, { packageIndex: draftIndex, taskGoal: lastAgent?.taskGoal });
          const task = result?.task;
          if (task?.id) AppTaskActions.openTodoTask(task.id);
          return;
        }
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
