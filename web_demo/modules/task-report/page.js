(function () {
  let lastReport = null;
  let lastAgent = null;
  const s = (value) => AppShell.escape(value ?? "");

  function arr(value) { return Array.isArray(value) ? value.filter(Boolean) : []; }
  function cleanPill(value) { const text = String(value || "").trim(); if (!text || text === "通用" || text === "ActionPlan" || /^AP-/i.test(text)) return ""; return text; }
  function setBusy(node, label = "处理中") { if (!node) return; node.dataset.originalText = node.dataset.originalText || node.textContent || ""; node.disabled = true; node.textContent = label; node.classList.add("is-loading"); }
  function restoreBusy(node) { if (!node) return; node.disabled = false; node.textContent = node.dataset.originalText || node.textContent || "重试"; node.classList.remove("is-loading"); }
  function localError(node, message) { if (!node?.parentElement) return; const old = node.parentElement.querySelector(".inline-action-error"); old?.remove?.(); const tip = document.createElement("span"); tip.className = "inline-action-error"; tip.textContent = message || "操作失败，请重试"; node.parentElement.appendChild(tip); }
  function pillRow(items = []) { const list = items.map(cleanPill).filter(Boolean); if (!list.length) return ""; return `<div class="action-package-pills">${list.map((item) => `<span>${s(item)}</span>`).join("")}</div>`; }
  function numberedList(items = []) { const list = arr(items); if (!list.length) return ""; return `<ol class="action-step-list">${list.map((item) => `<li>${s(item)}</li>`).join("")}</ol>`; }
  function chipList(items = []) { const list = arr(items); if (!list.length) return ""; return `<div class="action-chip-list">${list.map((item) => `<span>${s(item)}</span>`).join("")}</div>`; }
  function packagePanel(title, items = [], type = "chips") { const list = arr(items); if (!list.length) return ""; return `<div class="action-package-panel"><h5>${s(title)}</h5>${type === "steps" ? numberedList(list) : chipList(list)}</div>`; }
  function listBlock(title, items = [], options = {}) {
    const list = arr(items);
    if (!list.length) return "";
    const label = options.label || `${list.length} 项`;
    return `<section class="page-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${s(label)}</span></div><div class="report-card-list compact-report-list">${list.map((item, index) => {
      if (typeof item === "string") return `<article class="report-card compact"><strong>${index + 1}. ${s(item)}</strong></article>`;
      return `<article class="report-card compact"><strong>${s(item.title || item.label || `第 ${index + 1} 项`)}</strong><p>${s(item.value || item.summary || item.text || item.reason || "待确认")}</p></article>`;
    }).join("")}</div></section>`;
  }
  function evidenceBlock(items = []) { const list = arr(items); if (!list.length) return ""; return `<section class="page-section"><div class="section-header"><h3>数据证据</h3><span class="status-badge">可追溯</span></div><div class="kpi-grid report-metrics">${list.map((item) => `<article class="card report-metric-card"><h3>${s(item.label)}</h3><strong>${s(item.value)}</strong></article>`).join("")}</div></section>`; }
  function kvBlock(title, items = []) { const list = arr(items).filter((item) => item?.value !== undefined && item?.value !== null && item?.value !== ""); if (!list.length) return ""; return `<section class="page-section alert-evidence-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${list.length}</span></div><div class="alert-kv-grid">${list.map((item) => `<article><span>${s(item.label)}</span><strong>${s(item.value)}</strong></article>`).join("")}</div></section>`; }
  function triggerBlock(rule) { if (!rule) return ""; return `<section class="page-section alert-evidence-section"><div class="section-header"><h3>触发规则</h3><span class="status-badge">${s(rule.status || "已触发")}</span></div><div class="alert-rule-card"><strong>${s(rule.name || "报表预警")}</strong><p>${s(rule.rule || "命中当前规则阈值后触发。")}</p></div></section>`; }
  function responsibilityBlock(info) { if (!info?.store) return ""; const store = info.store; return `<section class="page-section alert-evidence-section"><div class="section-header"><h3>责任归属</h3><span class="status-badge">店铺权限</span></div><div class="alert-responsibility-grid"><article><span>责任店铺</span><strong>${s(store.storeName || "未绑定")}</strong></article><article><span>平台</span><strong>${s(store.platform || "待确认")}</strong></article><article><span>负责人</span><strong>${s(info.operatorName || store.operatorName || "待确认")}</strong></article><article><span>复核人</span><strong>${s(info.reviewerName || store.reviewerName || "店群总管")}</strong></article></div></section>`; }
  function rawRowsBlock(rows = []) { if (!rows.length) return ""; const headers = Array.from(new Set(rows.flatMap((row) => Object.keys(row || {})))).slice(0, 8); return `<section class="page-section alert-evidence-section"><div class="section-header"><h3>原始报表行</h3><span class="status-badge">${rows.length} 行</span></div><div class="report-preview-table"><table><thead><tr>${headers.map((header) => `<th>${s(header)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${headers.map((header) => `<td>${s(row?.[header] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section>`; }

  function lifecycleBlock(report) {
    const life = report?.taskLifecycle || {};
    const cycles = arr(report?.recapCycles || life.recapCycles);
    return `<section class="page-section alert-evidence-section"><div class="section-header"><h3>任务生命周期</h3><span class="status-badge">${s(life.stageLabel || life.stage || "生成任务")}</span></div><div class="alert-kv-grid"><article><span>当前阶段</span><strong>${s(life.stageLabel || life.stage || "生成任务")}</strong></article><article><span>下一步</span><strong>${s(life.nextExpected || report?.nextStep || "继续处理")}</strong></article><article><span>自动复盘</span><strong>${cycles.length ? `${cycles.length} 个周期` : "等待复核后生成"}</strong></article><article><span>RAG候选</span><strong>${report?.ragCandidate ? "已生成" : "未生成"}</strong></article></div>${cycles.length ? listBlock("自动复盘周期", cycles.map((item) => ({ title: item.label || item.cycle || item.dueIn || "复盘周期", summary: item.status || item.metricScope || item.recapTarget || "待系统读取后续数据" })), { label: `${cycles.length} 个周期` }) : ""}</section>`;
  }
  function affectedProductsBlock(report) {
    const list = arr(report?.affectedProducts);
    if (!list.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>关联商品</h3><span class="status-badge">${s(report.affectedProductCount || list.length)} 个商品</span></div><div class="report-card-list compact-report-list">${list.slice(0, 20).map((item, index) => `<article class="report-card compact"><strong>${index + 1}. ${s(item.title || item.productTitle || item.productName || item.productId || "商品")}</strong><p>${s(item.storeName || item.store || "店铺")} · ${s(item.platform || "平台")} · ${s(item.reason || item.status || "受该任务影响")}</p></article>`).join("")}</div></section>`;
  }
  function authorizationBlock(report) {
    const gate = report?.actionAuthorization || {};
    if (!Object.keys(gate).length) return "";
    const budget = gate.budgetGate || {};
    const impact = gate.impactGate || {};
    const items = [
      { label: "当前动作", value: gate.actionLabel || gate.actionType },
      { label: "审批判断", value: gate.decision || "运营执行" },
      { label: "判断原因", value: gate.approvalReason || gate.policy?.rule },
      { label: "预算范围", value: budget.operatorBudgetMax ? `${budget.operatorBudgetMin} - ${budget.operatorBudgetMax}` : "未触发预算闸门" },
      { label: "保守估算", value: impact.belowCompanyFloor ? "低于公司基线" : "未低于公司基线" },
    ];
    return kvBlock("权限与估算", items);
  }
  function isCreativeSignal(report) { const task = report?.relatedTask || {}; const text = [report?.title, report?.warningSummary, task?.title, task?.task, task?.riskDomain, task?.taskType, ...(task?.judgmentTags || [])].filter(Boolean).join(" "); return /点击|CTR|主图|标题|创意|转化/.test(text) && (task.productId || report?.entityId) && !task?.actionPlan; }
  function packageCard(pkg, index, productId, mode = "action") { const isCreative = mode === "creative"; const packageName = pkg.packageName || pkg.name || `方案 ${index + 1}`; const targetMetric = pkg.targetMetric || (isCreative ? "点击率 / 转化率" : "处理指标"); return `<article class="action-package-card"><div class="action-package-head"><div><span class="action-package-label">${isCreative ? "测试包" : "处理包"}</span><h4>${s(packageName)}</h4>${pkg.diagnosis ? `<p>${s(pkg.diagnosis)}</p>` : ""}</div><span class="status-badge">${s(targetMetric)}</span></div><div class="action-package-body">${packagePanel("运营动作", pkg.operatorAction, "steps")}${packagePanel("提交指标", pkg.submitMetrics)}${packagePanel("复核标准", pkg.acceptanceCriteria)}${packagePanel("失败阈值", pkg.failureThreshold)}${packagePanel("复核重点", pkg.reviewFocus)}</div>${pkg.risk ? `<div class="action-package-risk"><strong>风险提醒</strong><p>${s(pkg.risk)}</p></div>` : ""}${isCreative ? `<div class="report-actions"><button type="button" data-creative-task="${s(productId)}:${index}">选择此方案创建测试任务</button></div>` : ""}</article>`; }
  function actionPlanBlock(agent, report) { const suggestions = arr(agent?.structuredSteps || agent?.suggestions || report?.suggestedActions || report?.operationChecklist); if (!suggestions.length) return ""; return `<section class="page-section action-plan-section"><div class="section-header"><h3>处理步骤</h3><span class="status-badge">按任务执行</span></div><div class="action-package-list"><article class="action-package-card"><div class="action-package-head"><div><span class="action-package-label">运营动作</span><h4>当前执行要求</h4></div></div>${numberedList(suggestions.map((item) => item.title || item.action || item.summary || item))}</article></div></section>`; }
  function taskDraftBlock(agent) { return ""; }
  function llmBriefBlock(agent) { const cards = []; if (agent?.llmSummary) cards.push({ title: "判断补充", value: agent.llmSummary }); const risk = arr(agent?.llmRiskCheck); if (!cards.length && !risk.length) return ""; return `<section class="page-section llm-brief-section"><div class="section-header"><h3>方案补充</h3><span class="status-badge">已结合经验</span></div><div class="llm-brief-grid">${cards.map((item) => `<article><span>${s(item.title)}</span><strong>${s(item.value)}</strong></article>`).join("")}${risk.length ? `<article><span>风险提醒</span>${chipList(risk)}</article>` : ""}</div></section>`; }
  function agentBlock(agent, report) { return `${actionPlanBlock(agent, report)}${llmBriefBlock(agent)}${taskDraftBlock(agent)}`; }
  function actionButtons(report) { if (report.taskId) return `<button type="button" data-back>返回</button><button type="button" data-open-task="${s(report.taskId)}">查看待办任务</button>`; return `<button type="button" data-back>返回</button><button type="button" data-source="${s(report.sourceRoute)}">返回来源模块</button>`; }
  async function loadAgentForReport(report) { if (!report || report.fallbackDetail || report.structureMissing || report.failClosed) return null; try { const task = report.relatedTask || {}; if (isCreativeSignal(report) && (task.productId || report.entityId)) return await AppApi.creativeAgent(task.productId || report.entityId, { taskGoal: report.warningSummary || task.task || "提升点击率和转化率", platform: task.platform || "通用", categoryId: task.categoryId || "home_living_goods" }); if (report.taskId) return await AppApi.moduleAgent("task", report.taskId, "breakdown"); if (report.module && report.entityId) return await AppApi.moduleAgent(report.module, report.entityId, "analysis"); } catch (error) { console.warn("[task-report] agent load failed", error); } return null; }

  function renderReport(report) {
    if (!report) return `<section class="page-section"><h3>报告加载失败</h3><p>没有拿到任务报告。请回到来源模块重新打开。</p></section>`;
    const task = report.relatedTask || {};
    const metrics = [["来源模块", report.sourceModule || "任务系统", report.sourceRoute || "business-actions"], ["对象 ID", report.entityId || report.taskId || "当前任务", report.module || "task"], ["任务状态", report.taskStatus || "候选预警", task.deadline || "待确认"], ["当前视角", report.viewer?.roleName || "默认", report.insightDepth || "role"]];
    return `<section class="report-hero"><div><p class="eyebrow">TASK REPORT · ${s(report.sourceModule || "任务系统")}</p><h2>${s(report.title || "任务详情")}</h2><p>${s(report.warningSummary || "任务详情已生成。")}</p></div><div class="report-hero-side"><span>风险等级</span><strong>${s(report.riskLevel || "中")}</strong><small>${s(report.taskStatus || report.reportType || "任务")}</small></div></section><section class="kpi-grid report-metrics">${metrics.map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section>${lifecycleBlock(report)}${affectedProductsBlock(report)}${authorizationBlock(report)}${kvBlock("来源链路", report.sourceTrace || [])}${triggerBlock(report.triggerRule)}${responsibilityBlock(report.responsibility)}${evidenceBlock(report.evidence || [])}${rawRowsBlock(report.rawRows || [])}${listBlock("证据链", report.evidenceChain || [])}${agentBlock(lastAgent, report)}${listBlock("需要提交的数据", report.dataNeeded || [])}<section class="page-section"><div class="section-header"><h3>下一步</h3><span class="status-badge">${report.fallbackDetail ? "结构兜底" : "继续流转"}</span></div><p>${s(report.nextStep || "返回任务列表继续处理。")}</p><div class="report-actions">${actionButtons(report)}</div></section>`;
  }
  function rerenderCurrentReport() { AppShell.setView(renderReport(lastReport)); }

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
      ctx.delegate("[data-back]", "click", () => { const source = lastReport?.taskId ? "business-actions" : lastReport?.sourceRoute; AppRouter.navigate(source || "dashboard"); });
      ctx.delegate("[data-source]", "click", (_, node) => AppRouter.navigate(node.dataset.source || "dashboard"));
      ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask));
      ctx.delegate("[data-refresh-agent]", "click", async (_, node) => { setBusy(node, "生成中"); const previousAgent = lastAgent; const nextAgent = await loadAgentForReport(lastReport); if (nextAgent) { lastAgent = nextAgent; rerenderCurrentReport(); return; } lastAgent = previousAgent; restoreBusy(node); localError(node, "生成失败，已保留当前方案"); });
      ctx.delegate("[data-creative-task]", "click", async (_, node) => { const [productId, packageIndex] = (node.dataset.creativeTask || "").split(":"); setBusy(node, "创建中"); const result = await AppApi.createCreativeTask(productId, { packageIndex: Number(packageIndex || 0), taskGoal: lastAgent?.taskGoal, platform: lastAgent?.platformRule?.platform || lastAgent?.productFacts?.platform || "通用", categoryId: lastAgent?.categoryProfile?.categoryId || "home_living_goods" }); const task = result?.task; if (task?.id) AppTaskActions.openTodoTask(task.id); else { restoreBusy(node); localError(node, result?.message || "创建失败，请重试"); } });
    },
  };
})();
