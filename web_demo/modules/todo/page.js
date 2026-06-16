(function () {
  let notice = "";
  const s = (value) => AppShell.escape(value);

  function hasAction(task, action) { return (task.availableActions || []).includes(action); }
  function layerName(task) {
    const map = { owner_decision: "老板决策", review_audit: "复盘审计", cycle_draft: "周期草案", manager_dispatch: "总管调度", operator_execution: "运营执行", finance_check: "财务复核" };
    return map[task.taskLayer] || task.taskLayer || "任务流";
  }
  function scopeText(task) {
    const roles = task.visibleRoleIds?.length ? `可见角色：${task.visibleRoleIds.join("/")}` : "角色自动过滤";
    const stores = task.visibleStoreIds?.length || task.storeIds?.length ? `店铺范围：${[...(task.visibleStoreIds || task.storeIds || [])].join("/")}` : "全局范围";
    return `${roles} · ${stores}`;
  }
  function eventText(task) {
    if (!task.lastEventMessage && !task.recentEvents?.length) return "等待生命周期事件";
    const item = task.recentEvents?.[0];
    return task.lastEventMessage || item?.message || item?.eventLabel || "已同步";
  }
  function actionButtons(task) {
    const actions = [`<button type="button" data-task-report="${s(task.id)}">详情报告</button>`];
    if (hasAction(task, "assign")) actions.push(`<button type="button" data-split="${s(task.id)}">拆分子任务</button>`);
    if (hasAction(task, "assign")) actions.push(`<button type="button" data-assign="${s(task.id)}">派发给运营</button>`);
    if (hasAction(task, "accept")) actions.push(`<button type="button" class="primary" data-accept="${s(task.id)}">接收任务</button>`);
    if (hasAction(task, "submit")) actions.push(`<button type="button" class="primary" data-submit="${s(task.id)}">提交复核</button>`);
    if (hasAction(task, "review")) {
      actions.push(`<button type="button" class="primary" data-review="${s(task.id)}:approve">复核通过</button>`);
      actions.push(`<button type="button" data-review="${s(task.id)}:return">退回</button>`);
    }
    if (hasAction(task, "write_recap")) actions.push(`<button type="button" data-recap="${s(task.id)}">写入复盘</button>`);
    if (hasAction(task, "pin")) actions.push(`<button type="button" data-pin="${s(task.id)}">置顶</button>`);
    if (hasAction(task, "move")) {
      actions.push(`<button type="button" data-move="${s(task.id)}:up">上移</button>`);
      actions.push(`<button type="button" data-move="${s(task.id)}:down">下移</button>`);
    }
    actions.push(`<button type="button" data-go="${s(task.sourceRoute || "dashboard")}">来源</button>`);
    return actions.join("");
  }
  function row(task, index, focusTaskId = "") {
    const focused = focusTaskId && task.id === focusTaskId;
    const workflow = task.workflowStatus || task.status || "待派发";
    const viewer = task.viewerRoleName ? `<span>当前视角：${s(task.viewerRoleName)} · ${s(task.viewerInsightDepth || "role")}</span>` : "";
    return `<article class="todo-card ${focused ? "focused-task" : ""}" data-task-card="${s(task.id)}"><div class="todo-rank ${AppShell.statusClass(task.priorityLevel)}">${index + 1}</div><div class="todo-title-cell"><div class="todo-thumb">${s(task.imageLabel || "任")}</div><div class="todo-title-block"><strong>${s(task.title || task.productTitle)}</strong><small>${s(task.productId || task.id)} · ${s(task.platform || "经营单元")} · ${s(task.store || "任务池")}</small><span>来源：${s(task.source || task.sourceModule)} · 截止：${s(task.deadline)}</span><span>${s(layerName(task))} · ${s(scopeText(task))}</span><span>生命周期：${s(eventText(task))}</span>${viewer}</div></div><div class="todo-task-block"><span>任务</span><strong>${s(task.task || task.taskType || "处理经营任务")}</strong><small>${s(task.reason || "由服务端任务池按角色与店铺权限同步生成。")}</small></div><div class="todo-meta-strip"><div class="todo-number-cell ${AppShell.statusClass(task.priorityLevel)}"><span>优先级</span><strong>${s(task.priority)}</strong><small>${s(task.deadline)}</small></div><div class="todo-number-cell"><span>执行人</span><strong>${s(task.assigneeName || "未派发")}</strong><small>${s(task.assignedByName || "待总管拆分")}</small></div><div class="todo-number-cell warning"><span>状态</span><strong>${s(workflow)}</strong><small>${s(task.reviewerName || "待复核人")}</small></div></div><div class="todo-actions">${actionButtons(task)}</div></article>`;
  }
  function metrics(allTasks, activeTasks, counters = {}) {
    return [
      ["可见待办", counters.visibleActive ?? activeTasks.length, "按当前账号过滤"],
      ["待接收", counters.waitingAccept ?? activeTasks.filter((t) => ["待接收", "待确认"].includes(t.status)).length, "运营确认"],
      ["处理中", counters.processing ?? activeTasks.filter((t) => t.status === "处理中").length, "执行中"],
      ["待复核", counters.reviewing ?? activeTasks.filter((t) => t.status === "待复核").length, "总管复核"],
      ["已退回", counters.returned ?? activeTasks.filter((t) => t.workflowStatus === "已退回" || t.status === "已退回").length, "需补充"],
      ["待写复盘", counters.waitingRecap ?? activeTasks.filter((t) => t.status === "已完成").length, "日报 / 周报"],
      ["生命周期事件", counters.recentEvents ?? AppTaskStore.listEvents?.().length ?? 0, "跨账号同步"],
      ["已完成", allTasks.filter((t) => t.status === "已完成" || t.status === "已写入复盘").length, "进入日志追溯"],
    ];
  }
  function eventFeed(events = []) {
    const rows = events.slice(0, 6).map((item) => `<article class="todo-event-card"><strong>${s(item.eventLabel || item.eventType)}</strong><span>${s(item.actorName || "系统")} · ${s(item.message || "任务已同步")}</span><small>${s(item.fromStatus || "-")} → ${s(item.toStatus || "-")} · ${s(item.createdAt || "")}</small></article>`).join("");
    return `<section class="page-section todo-list-section"><div class="section-header"><h3>跨账号生命周期</h3><span class="status-badge">任务动作会同步相关账号</span></div><div class="todo-event-list">${rows || `<div class="todo-empty">暂无生命周期事件。</div>`}</div></section>`;
  }
  async function refresh(message) { await AppApi.refreshTaskState(); notice = message; AppRouter.schedule("todo-refresh"); }
  function focusTask(taskId) {
    if (!taskId) return;
    requestAnimationFrame(() => { const card = document.querySelector(`[data-task-card="${CSS.escape(taskId)}"]`); if (!card) return; card.scrollIntoView({ behavior: "smooth", block: "center" }); card.style.boxShadow = "0 0 0 4px rgba(67, 56, 202, 0.18)"; setTimeout(() => { card.style.boxShadow = ""; }, 1800); });
  }

  window.TodoPage = {
    route: "business-actions",
    title: "待办",
    render(ctx) {
      const focusTaskId = ctx?.state?.focusTaskId || "";
      const allTasks = AppTaskStore.listTasks();
      const tasks = AppTaskStore.listActiveTasks();
      const events = AppTaskStore.listEvents?.() || [];
      const counters = AppTaskStore.counters?.() || {};
      const user = AppApi.currentUser?.() || {};
      return `<section class="todo-toolbar"><div><p class="eyebrow">TASK CENTER · LIFECYCLE SYNC</p><h2>跨账号任务流</h2><p>当前以 ${s(user.roleName || "默认账号")} 查看任务。运营接收 / 提交后，总管账号会同步状态、数量、日志和生命周期事件。</p></div><div class="todo-filter-row"><button type="button" data-reset>重置演示</button></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid todo-metrics">${metrics(allTasks, tasks, counters).map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section>${eventFeed(events)}<section class="page-section todo-list-section"><div class="section-header"><h3>执行队列</h3><span class="status-badge">${tasks.length} 个可见待办</span></div><div class="todo-card-list">${tasks.length ? tasks.map((task, index) => row(task, index, focusTaskId)).join("") : `<div class="todo-empty">当前账号没有可见待办。老板看决策，总管看调度，运营看自己负责店铺内的任务。</div>`}</div></section>`;
    },
    mount(ctx) {
      focusTask(ctx.state?.focusTaskId);
      ctx.delegate("[data-task-report]", "click", (_, node) => AppTaskActions.openTaskReport(node.dataset.taskReport));
      ctx.delegate("[data-split]", "click", async (_, node) => { notice = "任务拆分中..."; AppRouter.schedule("todo-split-start"); await AppApi.splitTodo(node.dataset.split, { note: "总管拆分为运营可执行子任务" }); await refresh("任务已拆分为运营子任务，运营待接收，总管同步已拆分。"); });
      ctx.delegate("[data-assign]", "click", async (_, node) => { notice = "任务派发中..."; AppRouter.schedule("todo-assign-start"); await AppApi.assignTodo(node.dataset.assign, { note: "当前账号派发任务给运营账号" }); await refresh("任务已派发给运营，运营待接收，总管同步已派发。"); });
      ctx.delegate("[data-accept]", "click", async (_, node) => { notice = "接收任务中..."; AppRouter.schedule("todo-accept-start"); await AppApi.acceptTodo(node.dataset.accept, { note: "运营已接收任务。" }); await refresh("运营已接收任务；总管账号同步看到处理中。"); });
      ctx.delegate("[data-submit]", "click", async (_, node) => { notice = "运营提交中..."; AppRouter.schedule("todo-submit-start"); await AppApi.submitTodo(node.dataset.submit, { note: "运营已处理，提交店群总管复核。" }); await refresh("任务已提交复核；总管账号待复核 +1。"); });
      ctx.delegate("[data-review]", "click", async (_, node) => { const [id, decision] = node.dataset.review.split(":"); notice = "复核处理中..."; AppRouter.schedule("todo-review-start"); await AppApi.reviewTodo(id, { decision, note: decision === "approve" ? "复核通过，归档。" : "退回运营补充处理。" }); await refresh(decision === "approve" ? "复核通过；运营和总管同步归档。" : "任务已退回；运营账号同步需补充。"); });
      ctx.delegate("[data-recap]", "click", async (_, node) => { notice = "写入复盘中..."; AppRouter.schedule("todo-recap-start"); await AppApi.writeRecapTodo(node.dataset.recap, { recapTarget: "日报", note: "总管写入日报复盘。" }); await refresh("任务已写入复盘；老板复盘审计入口可见周期结果。"); });
      ctx.delegate("[data-pin]", "click", async (_, node) => { await AppApi.pinTodo(node.dataset.pin); await refresh("任务已置顶，相关账号排序同步。"); });
      ctx.delegate("[data-move]", "click", async (_, node) => { const [id, direction] = node.dataset.move.split(":"); const moved = await AppApi.reorderTodo(id, direction); await refresh(moved ? "任务顺序已调整，相关账号排序同步。" : "当前任务已经在边界位置。"); });
      ctx.delegate("[data-go]", "click", (_, node) => AppRouter.navigate(node.dataset.go));
      ctx.delegate("[data-reset]", "click", async () => { await AppApi.resetTodo(); await refresh("服务端演示任务池已按角色权限和生命周期事件重置。"); });
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();