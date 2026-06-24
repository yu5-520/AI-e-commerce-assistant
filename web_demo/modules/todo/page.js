(function () {
  let notice = "";
  const s = (value) => AppShell.escape(value ?? "");
  const a = (value) => Array.isArray(value) ? value.filter(Boolean) : [];

  function hasAction(task, action) { return (task.availableActions || []).includes(action); }
  function layerName(task) { const map = { owner_decision: "老板决策", review_audit: "复盘审计", cycle_draft: "周期草案", manager_dispatch: "总管调度", operator_execution: "运营执行", finance_check: "财务复核" }; return map[task.taskLayer] || task.taskLayer || "任务流"; }
  function scopeText(task) { return task.visibleStoreIds?.length || task.storeIds?.length ? `店铺范围：${[...(task.visibleStoreIds || task.storeIds || [])].join("/")}` : "全局范围"; }
  function eventText(task) { const item = task.recentEvents?.[0]; return task.lastEventMessage || item?.message || item?.eventLabel || "等待生命周期事件"; }
  function evidenceSummary(task) { const item = task.latestEvidenceRecord || (task.evidenceRecords || [])[0]; if (!item) return "暂无处理证据"; return `${item.action || "处理"} · ${item.summary || item.result || "已提交"}`; }
  function selectedPath(task) { return task.selectedDecisionPath || {}; }
  function pathActions(task) { return a(selectedPath(task).actions).length ? a(selectedPath(task).actions) : [task.actionType || "执行已选路径", "提交处理结果", "等待复盘"]; }
  function reviewMetrics(task) { const path = selectedPath(task); return a(path.reviewMetrics).length ? a(path.reviewMetrics) : a(task.reviewPlan?.reviewMetrics).length ? a(task.reviewPlan.reviewMetrics) : ["处理结果", "下一轮数据变化", "复核结论"]; }
  function supplementChips(task) { const rows = Object.entries(task.operatorSupplement || {}).filter(([, value]) => value !== undefined && value !== null && value !== ""); if (!rows.length) return ""; return `<div class="todo-supplement-list">${rows.map(([key, value]) => `<span>${s(key)}：${s(value)}</span>`).join("")}</div>`; }

  function actionButton(task, item, fallbackClass = "") {
    if (!item?.action) return "";
    const cls = item.primary ? "primary" : fallbackClass;
    const id = s(task.id);
    const label = s(item.label || item.action);
    const action = item.action;
    if (action === "view") return `<button type="button" class="${cls}" data-task-report="${id}">${label}</button>`;
    if (action === "follow") return `<button type="button" class="${cls}" data-task-report="${id}">${label}</button>`;
    if (action === "confirm") return `<button type="button" class="${cls}" data-complete="${id}">${label}</button>`;
    if (action === "dispatch") return `<button type="button" class="${cls}" data-assign="${id}">${label}</button>`;
    if (action === "approve") return `<button type="button" class="${cls}" data-review-evidence="${id}:approve">${label}</button>`;
    if (action === "reject") return `<button type="button" class="${cls}" data-review-evidence="${id}:return">${label}</button>`;
    if (action === "accept") return `<button type="button" class="${cls}" data-accept="${id}">${label}</button>`;
    if (action === "submit") return `<button type="button" class="${cls}" data-submit-evidence="${id}">${label}</button>`;
    if (action === "supplement") return `<button type="button" class="${cls}" data-submit-evidence="${id}">${label}</button>`;
    return "";
  }

  function actionButtons(task) {
    const primary = actionButton(task, task.primaryTaskAction);
    const secondary = actionButton(task, task.secondaryTaskAction, "secondary");
    const detail = task.primaryTaskAction?.action === "view" ? "" : `<button type="button" data-task-report="${s(task.id)}">详情</button>`;
    return [primary, secondary, detail].filter(Boolean).join("");
  }

  function sopPanel(task) {
    const sop = task.taskExecutionSop || {};
    const steps = a(sop.executionSteps);
    if (!steps.length) return "";
    const rows = steps.map((item) => `<article class="todo-sop-step"><strong>${s(item.stepNo)}、${s(item.deadlineLabel || `${item.deadlineHours || "—"} 小时内`)} · ${s(item.ownerRole || "运营")}</strong><p>${s(item.action)}</p><div class="action-chip-list">${a(item.requiredEvidence).map((x) => `<span>${s(x)}</span>`).join("")}</div><small>复核：${s(item.reviewRule || "按证据复核")}</small></article>`).join("");
    const gate = task.completionGate || sop.completionGate || {};
    const gateText = gate.rule ? `<div class="todo-sop-gate"><strong>完成门槛</strong><span>${s(gate.rule)}</span></div>` : "";
    return `<div class="todo-sop-panel"><div class="section-header compact"><h3>${s(sop.sopName || "执行 SOP")}</h3><span class="status-badge">V10.13</span></div>${rows}${gateText}</div>`;
  }

  function evidencePanel(task) {
    if (!hasAction(task, "submit") && !hasAction(task, "review") && !(task.evidenceRecords || []).length) return "";
    const sopFields = a(task.executionSteps).flatMap((step) => a(step.submitFields)).slice(0, 8);
    const actionOptions = pathActions(task).map((item) => `<option value="${s(item)}">${s(item)}</option>`).join("");
    const metricSource = sopFields.length ? sopFields : reviewMetrics(task);
    const metricInputs = metricSource.map((metric) => `<label><span>${s(metric)}</span><input data-evidence-field="${s(metric)}" placeholder="填写处理后的结果或观察值" /></label>`).join("");
    const path = selectedPath(task);
    const pathSummary = path.pathName ? `<div class="todo-path-summary"><span>当前路径</span><strong>${s(path.pathName)}</strong><div class="action-chip-list">${a(path.reviewMetrics).map((x) => `<span>${s(x)}</span>`).join("")}</div>${supplementChips(task)}</div>` : "";
    const submitForm = hasAction(task, "submit") ? `<div class="task-evidence-form"><div class="section-header compact"><h3>执行证据</h3><span class="status-badge">提交复核</span></div>${pathSummary}<div class="task-evidence-grid"><label><span>执行动作</span><select data-evidence-action>${actionOptions}</select></label><label><span>处理结果</span><input data-evidence-result placeholder="例如：已整理退款 Top5 / 已核实客服原因" /></label><label class="wide"><span>成果说明</span><textarea data-evidence-summary placeholder="填写你实际做了什么、结果是什么、是否还需要下一轮复盘"></textarea></label>${metricInputs}<label class="wide"><span>截图 / 链接 / 记录</span><input data-evidence-link placeholder="截图链接、客服记录、退款原因表、详情页截图、报表行号或备注" /></label></div></div>` : "";
    const reviewForm = hasAction(task, "review") ? `<div class="task-review-form"><div class="section-header compact"><h3>总管复核</h3><span class="status-badge">${s(evidenceSummary(task))}</span></div><textarea data-review-comment placeholder="填写复核意见；证据不足时说明退回原因"></textarea></div>` : "";
    const latest = (task.evidenceRecords || []).length ? `<div class="task-evidence-history"><strong>最近证据</strong><span>${s(evidenceSummary(task))}</span></div>` : "";
    return `<div class="task-evidence-panel">${latest}${submitForm}${reviewForm}</div>`;
  }

  function row(task, index, focusTaskId = "") {
    const focused = focusTaskId && task.id === focusTaskId;
    const workflow = task.displayStatus || task.workflowStatus || task.status || "待派发";
    const viewer = task.viewerRoleName ? `<span>当前视角：${s(task.viewerRoleName)} · ${s(task.roleSurface || task.viewerInsightDepth || "role")}</span>` : "";
    const nextTarget = task.crossAccountFlow?.nextSyncTarget?.label ? `<span>下一同步：${s(task.crossAccountFlow.nextSyncTarget.label)}</span>` : "";
    return `<article class="todo-card ${focused ? "focused-task" : ""}" data-task-card="${s(task.id)}"><div class="todo-rank ${AppShell.statusClass(task.priorityLevel)}">${index + 1}</div><div class="todo-title-cell"><div class="todo-thumb">${s(task.imageLabel || "任")}</div><div class="todo-title-block"><strong>${s(task.title || task.productTitle)}</strong><small>${s(task.productId || task.id)} · ${s(task.platform || "经营单元")} · ${s(task.store || "任务池")}</small><span>来源：${s(task.source || task.sourceModule)} · 截止：${s(task.deadline)}</span><span>${s(layerName(task))} · ${s(scopeText(task))}</span><span>生命周期：${s(eventText(task))}</span>${viewer}${nextTarget}</div></div><div class="todo-task-block"><span>任务</span><strong>${s(task.task || task.taskType || "处理经营任务")}</strong><small>${s(task.roleSummary || task.reason || "由服务端任务池按角色与店铺权限同步生成。")}</small></div><div class="todo-meta-strip"><div class="todo-number-cell ${AppShell.statusClass(task.priorityLevel)}"><span>优先级</span><strong>${s(task.priority)}</strong><small>${s(task.deadline)}</small></div><div class="todo-number-cell"><span>执行人</span><strong>${s(task.assigneeName || "未派发")}</strong><small>${s(task.assignedByName || "系统路径确认")}</small></div><div class="todo-number-cell warning"><span>当前视图</span><strong>${s(workflow)}</strong><small>${s(task.reviewerName || "待复核人")}</small></div></div>${sopPanel(task)}${evidencePanel(task)}<div class="todo-actions v106-minimal-actions">${actionButtons(task)}</div></article>`;
  }

  function metrics(allTasks, activeTasks, counters = {}) { return [["可见待办", counters.visibleActive ?? activeTasks.length, "当前账号"], ["处理中", counters.processing ?? activeTasks.filter((t) => t.status === "处理中").length, "执行中"], ["待复核", counters.reviewing ?? activeTasks.filter((t) => t.status === "待复核").length, "总管复核"], ["已退回", counters.returned ?? activeTasks.filter((t) => t.workflowStatus === "已退回" || t.status === "已退回").length, "需补充"], ["生命周期事件", counters.recentEvents ?? AppTaskStore.listEvents?.().length ?? 0, "跨账号同步"], ["已完成", allTasks.filter((t) => t.status === "已完成" || t.status === "已写入复盘").length, "进入日志"]]; }
  function eventFeed(events = []) { const rows = events.slice(0, 6).map((item) => `<article class="todo-event-card"><strong>${s(item.eventLabel || item.eventType)}</strong><span>${s(item.actorName || "系统")} · ${s(item.message || "任务已同步")}</span><small>${s(item.fromStatus || "-")} → ${s(item.toStatus || "-")} · ${s(item.createdAt || "")}</small></article>`).join(""); return `<section class="page-section todo-list-section"><div class="section-header"><h3>跨账号生命周期</h3><span class="status-badge">同一任务多账号视图</span></div><div class="todo-event-list">${rows || `<div class="todo-empty">暂无生命周期事件。</div>`}</div></section>`; }
  async function refresh(message) { await AppApi.refreshTaskState(); notice = message; AppRouter.schedule("todo-refresh"); }
  function focusTask(taskId) { if (!taskId) return; requestAnimationFrame(() => { const card = document.querySelector(`[data-task-card="${CSS.escape(taskId)}"]`); if (!card) return; card.scrollIntoView({ behavior: "smooth", block: "center" }); card.style.boxShadow = "0 0 0 4px rgba(67, 56, 202, 0.18)"; setTimeout(() => { card.style.boxShadow = ""; }, 1800); }); }
  function taskCard(taskId) { return document.querySelector(`[data-task-card="${CSS.escape(taskId)}"]`); }
  function collectEvidence(taskId) { const card = taskCard(taskId); const fields = {}; card?.querySelectorAll("[data-evidence-field]").forEach((node) => { if (node.value) fields[node.dataset.evidenceField] = node.value; }); const link = card?.querySelector("[data-evidence-link]")?.value || ""; return { action: card?.querySelector("[data-evidence-action]")?.value || "路径执行", result: card?.querySelector("[data-evidence-result]")?.value || "已处理，待复核", summary: card?.querySelector("[data-evidence-summary]")?.value || "已按 SOP 处理，并提交执行证据。", formFields: fields, evidenceLinks: link ? [link] : [], needFollowUp: false, enterRecap: false }; }
  function collectReview(taskId, decision) { const card = taskCard(taskId); return { decision, comment: card?.querySelector("[data-review-comment]")?.value || (decision === "approve" ? "证据充分，复核通过。" : "证据不足，退回补充。") }; }

  window.TodoPage = { route: "business-actions", title: "待办", render(ctx) { const focusTaskId = ctx?.state?.focusTaskId || ""; const allTasks = AppTaskStore.listTasks(); const tasks = AppTaskStore.listActiveTasks(); const events = AppTaskStore.listEvents?.() || []; const counters = AppTaskStore.counters?.() || {}; const user = AppApi.currentUser?.() || {}; return `<section class="todo-toolbar"><div><p class="eyebrow">TASK CENTER · SOP WORK ORDERS</p><h2>任务处理</h2><p>当前以 ${s(user.roleName || "默认账号")} 查看任务。任务必须按 SOP 提交证据，不能只写处理建议。</p></div><div class="todo-filter-row"><button type="button" data-reset>重置运行态</button></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid todo-metrics">${metrics(allTasks, tasks, counters).map(([x,y,z]) => AppShell.metricCard(x,y,z)).join("")}</section>${eventFeed(events)}<section class="page-section todo-list-section"><div class="section-header"><h3>执行队列</h3><span class="status-badge">${tasks.length} 个可见待办</span></div><div class="todo-card-list">${tasks.length ? tasks.map((task, index) => row(task, index, focusTaskId)).join("") : `<div class="todo-empty">当前账号没有可见待办。</div>`}</div></section>`; }, mount(ctx) { focusTask(ctx.state?.focusTaskId); ctx.delegate("[data-task-report]", "click", (_, node) => AppTaskActions.openTaskReport(node.dataset.taskReport)); ctx.delegate("[data-assign]", "click", async (_, node) => { await AppApi.assignTodo(node.dataset.assign, { note: "派发任务给运营账号" }); await refresh("任务已派发。"); }); ctx.delegate("[data-accept]", "click", async (_, node) => { await AppApi.acceptTodo(node.dataset.accept, { note: "运营已接收任务" }); await refresh("任务已接收，进入处理中。"); }); ctx.delegate("[data-submit-evidence]", "click", async (_, node) => { await AppApi.submitEvidenceTodo(node.dataset.submitEvidence, collectEvidence(node.dataset.submitEvidence)); await refresh("执行证据已提交，等待总管复核。"); }); ctx.delegate("[data-review-evidence]", "click", async (_, node) => { const [taskId, decision] = node.dataset.reviewEvidence.split(":"); await AppApi.reviewEvidenceTodo(taskId, collectReview(taskId, decision)); await refresh(decision === "approve" ? "复核通过。" : "已退回补充。"); }); ctx.delegate("[data-complete]", "click", async (_, node) => { await AppApi.completeTodo(node.dataset.complete); await refresh("任务已确认。"); }); ctx.delegate("[data-reset]", "click", async () => { await AppApi.resetRuntimeData?.(); await refresh("运行态已清空。"); }); ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("todo-store"))); } };
})();