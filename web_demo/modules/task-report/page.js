(function () {
  let lastReport = null;
  let lastAgent = null;
  const s = (value) => AppShell.escape(value ?? "");

  function arr(value) {
    return Array.isArray(value) ? value.filter(Boolean) : [];
  }

  function cleanPill(value) {
    const text = String(value || "").trim();
    if (!text || text === "通用" || text === "ActionPlan" || /^AP-/i.test(text)) return "";
    return text;
  }

  function setBusy(node, label = "处理中") {
    if (!node) return;
    node.dataset.originalText = node.dataset.originalText || node.textContent || "";
    node.disabled = true;
    node.textContent = label;
    node.classList.add("is-loading");
  }

  function restoreBusy(node) {
    if (!node) return;
    node.disabled = false;
    node.textContent = node.dataset.originalText || node.textContent || "重试";
    node.classList.remove("is-loading");
  }

  function localError(node, message) {
    if (!node?.parentElement) return;
    const old = node.parentElement.querySelector(".inline-action-error");
    old?.remove?.();
    const tip = document.createElement("span");
    tip.className = "inline-action-error";
    tip.textContent = message || "操作失败，请重试";
    node.parentElement.appendChild(tip);
  }

  function pillRow(items = []) {
    const list = items.map(cleanPill).filter(Boolean);
    if (!list.length) return "";
    return `<div class="action-package-pills">${list.map((item) => `<span>${s(item)}</span>`).join("")}</div>`;
  }

  function numberedList(items = []) {
    const list = arr(items);
    if (!list.length) return "";
    return `<ol class="action-step-list">${list.map((item) => `<li>${s(item)}</li>`).join("")}</ol>`;
  }

  function chipList(items = []) {
    const list = arr(items);
    if (!list.length) return "";
    return `<div class="action-chip-list">${list.map((item) => `<span>${s(item)}</span>`).join("")}</div>`;
  }

  function packagePanel(title, items = [], type = "chips") {
    const list = arr(items);
    if (!list.length) return "";
    return `<div class="action-package-panel"><h5>${s(title)}</h5>${type === "steps" ? numberedList(list) : chipList(list)}</div>`;
  }

  function listBlock(title, items = [], options = {}) {
    const list = arr(items);
    if (!list.length) return "";
    const label = options.label || `${list.length} 项`;
    return `<section class="page-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${s(label)}</span></div><div class="report-card-list compact-report-list">${list.map((item, index) => {
      if (typeof item === "string") return `<article class="report-card compact"><strong>${index + 1}. ${s(item)}</strong></article>`;
      return `<article class="report-card compact"><strong>${s(item.title || item.label || `第 ${index + 1} 项`)}</strong><p>${s(item.value || item.summary || item.text || item.reason || "待确认")}</p></article>`;
    }).join("")}</div></section>`;
  }

  function evidenceBlock(items = []) {
    const list = arr(items);
    if (!list.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>数据证据</h3><span class="status-badge">可追溯</span></div><div class="kpi-grid report-metrics">${list.map((item) => `<article class="card report-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`).join("")}</div></section>`;
  }

  function kvBlock(title, items = []) {
    const list = arr(items).filter((item) => item?.value !== undefined && item?.value !== null && item?.value !== "");
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
    return /点击|CTR|主图|标题|创意|转化/.test(text) && (task.productId || report?.entityId) && !task?.actionPlan;
  }

  function packageCard(pkg, index, productId, mode = "action") {
    const isCreative = mode === "creative";
    const packageName = pkg.packageName || pkg.name || `方案 ${index + 1}`;
    const mainTitle = pkg.llmTitle || pkg.title;
    const imageDirection = pkg.llmMainImageDirection || pkg.mainImageDirection;
    const firstImageText = pkg.llmFirstImageText || pkg.firstImageText;
    const imageLayout = pkg.llmMainImageLayout || pkg.mainImageLayout;
    const sellingPoints = arr(pkg.sellingPointOrder);
    const targetMetric = pkg.targetMetric || (isCreative ? "点击率 / 转化率" : "处理指标");
    return `<article class="action-package-card ${isCreative ? "creative" : ""}">
      <div class="action-package-head">
        <div>
          <span class="action-package-label">${isCreative ? "测试包" : "处理包"}</span>
          <h4>${s(packageName)}</h4>
          ${pkg.diagnosis ? `<p>${s(pkg.diagnosis)}</p>` : ""}
        </div>
        <span class="status-badge">${s(targetMetric)}</span>
      </div>
      ${pillRow([pkg.testDuration, pkg.fitTraffic, pkg.fitPlatform, pkg.style])}
      ${isCreative && (mainTitle || imageDirection || firstImageText) ? `<div class="creative-preview-grid"><article><span>标题</span><strong>${s(mainTitle || "待生成")}</strong></article><article><span>主图方向</span><strong>${s(imageDirection || "待生成")}</strong><small>${s(imageLayout || "")}</small></article><article><span>首图文案</span><strong>${s(firstImageText || "待生成")}</strong></article>${sellingPoints.length ? `<article><span>卖点顺序</span><strong>${s(sellingPoints.join(" → "))}</strong></article>` : ""}</div>` : ""}
      <div class="action-package-body">
        ${packagePanel("运营动作", pkg.operatorAction, "steps")}
        ${packagePanel("提交指标", pkg.submitMetrics)}
        ${packagePanel("复核标准", pkg.acceptanceCriteria)}
        ${packagePanel("失败阈值", pkg.failureThreshold)}
        ${packagePanel("复核重点", pkg.reviewFocus)}
      </div>
      ${pkg.risk ? `<div class="action-package-risk"><strong>风险提醒</strong><p>${s(pkg.risk)}</p></div>` : ""}
      ${isCreative ? `<div class="report-actions"><button type="button" data-creative-task="${s(productId)}:${index}">选择此方案创建测试任务</button></div>` : ""}
    </article>`;
  }

  function testPackagesBlock(agent) {
    const packages = arr(agent?.llmPackagePreviews).length ? agent.llmPackagePreviews : arr(agent?.testPackages);
    if (!packages.length) return "";
    return `<section class="page-section action-plan-section"><div class="section-header"><h3>Agent 测试包</h3><span class="status-badge">运营上架测试</span></div><div class="action-package-list">${packages.map((pkg, index) => packageCard(pkg, index, agent.productId || lastReport?.relatedTask?.productId || lastReport?.entityId, "creative")).join("")}</div></section>`;
  }

  function executionPackagesBlock(agent) {
    const packages = arr(agent?.executionPackages).length ? agent.executionPackages : arr(agent?.actionPlan?.executionPackages);
    if (!packages.length) return "";
    return `<section class="page-section action-plan-section"><div class="section-header"><h3>问题处理包</h3><span class="status-badge">${s(agent?.actionPlan?.problemLabel || agent?.problemLabel || "按问题类型生成")}</span></div><div class="action-package-list">${packages.map((pkg, index) => packageCard(pkg, index, agent?.productId || lastReport?.relatedTask?.productId || lastReport?.entityId, "action")).join("")}</div></section>`;
  }

  function actionPlanBlock(agent, report) {
    if (arr(agent?.testPackages).length) return testPackagesBlock(agent);
    if (arr(agent?.executionPackages).length || arr(agent?.actionPlan?.executionPackages).length) return executionPackagesBlock(agent);
    const suggestions = arr(agent?.structuredSteps || agent?.suggestions || report?.suggestedActions);
    if (!suggestions.length) return "";
    return `<section class="page-section action-plan-section"><div class="section-header"><h3>Agent 处理方案</h3><span class="status-badge">转成运营动作</span></div><div class="action-package-list"><article class="action-package-card"><div class="action-package-head"><div><span class="action-package-label">处理步骤</span><h4>运营动作</h4></div></div>${numberedList(suggestions.map((item) => item.title || item.action || item.summary || item))}</article></div></section>`;
  }

  function taskDraftCard(draft, index, sourceKey) {
    const steps = arr(draft.executionSteps);
    const evidence = arr(draft.evidenceRequired);
    const metrics = arr(draft.submitMetrics);
    const criteria = arr(draft.acceptanceCriteria);
    const failure = arr(draft.failureThreshold);
    const pkg = draft.selectedPackage || {};
    return `<article class="task-draft-card">
      <div class="task-draft-head">
        <div>
          <span class="action-package-label">即将加入待办</span>
          <h4>${s(draft.title || draft.taskType || "任务草案")}</h4>
          <p>${s(draft.task || draft.reason || "人工确认后进入任务池。")}</p>
        </div>
        <span class="status-badge">${s(draft.priority || "待确认")}</span>
      </div>
      <div class="task-draft-meta">
        <article><span>处理包</span><strong>${s(pkg.packageName || draft.actionType || "待选择")}</strong></article>
        <article><span>截止时间</span><strong>${s(draft.deadline || "待确认")}</strong></article>
        <article><span>来源</span><strong>${s(draft.sourceModule || draft.entityType || "经营模块")}</strong></article>
        <article><span>风险域</span><strong>${s(draft.riskDomain || "待确认")}</strong></article>
      </div>
      <div class="task-draft-grid">
        ${packagePanel("执行动作", steps, "steps")}
        ${packagePanel("提交材料", [...evidence, ...metrics])}
        ${packagePanel("验收标准", criteria)}
        ${packagePanel("失败阈值", failure)}
      </div>
      <div class="report-actions"><button type="button" data-agent-task="${s(sourceKey)}:${index}">确认加入任务清单</button></div>
    </article>`;
  }

  function taskDraftBlock(agent) {
    const drafts = arr(agent?.taskDrafts).length ? agent.taskDrafts : (agent?.taskDraft ? [agent.taskDraft] : []);
    if (!drafts.length) return "";
    const sourceKey = `${agent.module || "creative"}:${agent.entityId || agent.productId || lastReport?.entityId}`;
    return `<section class="page-section task-draft-section"><div class="section-header"><h3>任务草案</h3><span class="status-badge">人工确认后加入</span></div><div class="task-draft-list">${drafts.map((draft, index) => taskDraftCard(draft, index, sourceKey)).join("")}</div></section>`;
  }

  function agentBlock(agent, report) {
    if (!agent) return "";
    const evidence = arr(agent.evidence);
    const humanDecision = arr(agent.humanDecision || report.humanDecision);
    return `<section class="page-section"><div class="section-header"><h3>Agent 判断</h3><span class="status-badge">${s(agent.agentName || "Agent")}</span></div><p class="agent-summary-text">${s(agent.categoryStrategy || agent.summary || "已生成处理方案。")}</p>${evidence.length ? `<div class="kpi-grid report-metrics">${evidence.slice(0, 4).map((item) => `<article class="card report-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`).join("")}</div>` : ""}</section>${actionPlanBlock(agent, report)}${taskDraftBlock(agent)}${humanDecision.length ? `<section class="page-section"><div class="section-header"><h3>人工确认</h3><span class="status-badge">${humanDecision.length} 项</span></div>${chipList(humanDecision)}<div class="report-actions"><button type="button" data-refresh-agent>重新生成 Agent 方案</button></div></section>` : ""}`;
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
    return `<section class="report-hero"><div><p class="eyebrow">TASK REPORT · ${s(report.sourceModule)}</p><h2>${s(report.title)}</h2><p>${s(report.warningSummary)}</p></div><div class="report-hero-side"><span>风险等级</span><strong>${s(report.riskLevel)}</strong><small>${s(report.taskStatus || report.reportType)}</small></div></section><section class="kpi-grid report-metrics">${metrics.map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section>${kvBlock("来源链路", report.sourceTrace || [])}${triggerBlock(report.triggerRule)}${responsibilityBlock(report.responsibility)}${evidenceBlock(report.evidence || [])}${rawRowsBlock(report.rawRows || [])}${listBlock("证据链", report.evidenceChain || [])}${agentBlock(lastAgent, report)}${listBlock("需要补充的数据", report.dataNeeded || [])}<section class="page-section"><div class="section-header"><h3>下一步</h3><span class="status-badge">人工确认</span></div><p>${s(report.nextStep)}</p><div class="report-actions">${actionButtons(report)}</div></section>`;
  }

  function rerenderCurrentReport() {
    AppShell.setView(renderReport(lastReport));
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
      else lastReport = lastReport || null;
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
      ctx.delegate("[data-refresh-agent]", "click", async (_, node) => {
        setBusy(node, "生成中");
        const previousAgent = lastAgent;
        const nextAgent = await loadAgentForReport(lastReport);
        if (nextAgent) {
          lastAgent = nextAgent;
          rerenderCurrentReport();
          return;
        }
        lastAgent = previousAgent;
        restoreBusy(node);
        localError(node, "生成失败，已保留当前方案");
      });
      ctx.delegate("[data-creative-task]", "click", async (_, node) => {
        const [productId, packageIndex] = (node.dataset.creativeTask || "").split(":");
        setBusy(node, "创建中");
        const result = await AppApi.createCreativeTask(productId, { packageIndex: Number(packageIndex || 0), taskGoal: lastAgent?.taskGoal, platform: lastAgent?.platformRule?.platform || lastAgent?.productFacts?.platform || "通用", categoryId: lastAgent?.categoryProfile?.categoryId || "home_living_goods" });
        const task = result?.task;
        if (task?.id) AppTaskActions.openTodoTask(task.id);
        else {
          restoreBusy(node);
          localError(node, result?.message || "创建失败，请重试");
        }
      });
      ctx.delegate("[data-agent-task]", "click", async (_, node) => {
        const parts = (node.dataset.agentTask || "").split(":");
        const module = parts[0];
        const entityId = parts[1];
        const draftIndex = Number(parts[2] || 0);
        setBusy(node, "创建中");
        if (module === "creative") {
          const result = await AppApi.createCreativeTask(entityId, { packageIndex: draftIndex, taskGoal: lastAgent?.taskGoal });
          const task = result?.task;
          if (task?.id) AppTaskActions.openTodoTask(task.id);
          else {
            restoreBusy(node);
            localError(node, result?.message || "创建失败，请重试");
          }
          return;
        }
        const result = await AppApi.createAgentTask(module, entityId, draftIndex, lastAgent?.mode || "analysis");
        const task = result?.task;
        if (task?.id) AppTaskActions.openTodoTask(task.id);
        else {
          restoreBusy(node);
          localError(node, result?.message || "创建失败，请重试");
        }
      });
      ctx.delegate("[data-create-task]", "click", async (_, node) => {
        const [module, entityId] = node.dataset.createTask.split(":");
        setBusy(node, "创建中");
        const result = await AppTaskActions.createTaskFromReport(module, entityId);
        const task = result?.task;
        if (task?.id) AppTaskActions.openTodoTask(task.id);
        else {
          restoreBusy(node);
          localError(node, result?.message || "创建失败，请重试");
        }
      });
    },
  };
})();
