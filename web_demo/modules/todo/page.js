(function () {
  let notice = "";
  const s = (value) => AppShell.escape(value ?? "");

  function hasAction(task, action) { return (task.availableActions || []).includes(action); }
  function queueName(task) {
    const map = { urgent_execution: "紧急", today_execution: "今日", daily_operating_task: "今日经营", weekly_review_task: "周期复盘", candidate_only: "候选", report_seed_only: "报告素材" };
    return map[task.queueType] || "执行";
  }
  function layerName(task) {
    const map = { manager_dispatch: "主管确认", operator_execution: "运营执行", owner_decision: "老板确认", finance_check: "财务复核" };
    return map[task.taskLayer] || task.taskLayer || "任务";
  }
  function actionDecision(task) {
    const gate = task.actionAuthorization || task.v126ActionGate || {};
    const map = { auto_execute: "自动执行", manager_approval_required: "主管确认", owner_approval_required: "老板确认" };
    return map[gate.decision] || layerName(task);
  }
  function visibleTaskQueue(tasks) {
    return tasks.filter((task) => !["backend_tag", "store_product_tag", "observe_candidate", "candidate_only", "report_seed_only"].includes(task.queueType) && task.displayState !== "backend_only");
  }
  function deadlineRank(task) {
    const text = String(task.deadline || task.timeBucket || "");
    if (text.includes("2小时")) return 1;
    if (text.includes("6小时")) return 2;
    if (text.includes("12小时")) return 3;
    if (text.includes("今日")) return 4;
    if (text.includes("3天")) return 5;
    if (text.includes("本周") || text.includes("7天")) return 6;
    return 9;
  }
  function priorityRank(task) { return { 高: 1, 中: 2, 低: 3 }[task.priority] || 9; }
  function sortTasks(tasks) { return [...tasks].sort((a, b) => priorityRank(a) - priorityRank(b) || deadlineRank(a) - deadlineRank(b) || String(a.createdAt || "").localeCompare(String(b.createdAt || ""))); }
  function metrics(allTasks, activeTasks, counters = {}) {
    const visible = visibleTaskQueue(activeTasks);
    return [["执行任务", counters.visibleActive ?? visible.length, "后端任务池"], ["紧急/高", visible.filter((t) => t.priority === "高").length, "优先处理"], ["主管确认", visible.filter((t) => t.taskLayer === "manager_dispatch").length, "权限闸门"], ["处理中", counters.processing ?? visible.filter((t) => t.status === "处理中").length, "执行中"], ["待复核", counters.reviewing ?? visible.filter((t) => t.status === "待复核").length, "总管复核"]];
  }
  function openTaskReport(taskId) { AppRouter.navigate("task-report", { taskId }); }
  function taskBasis(task) {
    const gate = task.actionAuthorization || task.v126ActionGate || {};
    if (gate.approvalReason) return gate.approvalReason;
    return task.reason || task.taskSignal || "由服务端任务队列按风险和时效排序生成。";
  }
  function actionButtons(task) {
    const id = s(task.id);
    const buttons = [`<button type="button" data-task-report="${id}">查看详情</button>`];
    if (hasAction(task, "accept")) buttons.unshift(`<button type="button" class="primary" data-accept="${id}">接收</button>`);
    if (hasAction(task, "submit")) buttons.unshift(`<button type="button" class="primary" data-task-report="${id}">提交证据</button>`);
    if (hasAction(task, "assign")) buttons.unshift(`<button type="button" class="primary" data-assign="${id}">派发</button>`);
    if (hasAction(task, "review")) buttons.unshift(`<button type="button" class="primary" data-task-report="${id}">复核</button>`);
    return buttons.join("");
  }
  function row(task, index, focusTaskId = "") {
    const focused = focusTaskId && task.id === focusTaskId;
    const workflow = task.displayStatus || task.workflowStatus || task.status || "待处理";
    const gate = task.actionAuthorization || task.v126ActionGate || {};
    return `<article class="todo-card compact-task-card ${focused ? "focused-task" : ""}" data-task-card="${s(task.id)}">
      <div class="todo-rank ${AppShell.statusClass(task.priorityLevel)}">${index + 1}</div>
      <div class="todo-title-cell"><div class="todo-thumb">${s(task.imageLabel || "任")}</div><div class="todo-title-block"><strong>${s(task.title || task.productTitle)}</strong><small>${s(task.store || task.storeName || "任务池")} · ${s(task.platform || "经营单元")} · ${s(task.productId || task.entityId || task.id)}</small><span>${s(queueName(task))} · ${s(actionDecision(task))} · ${s(workflow)}</span></div></div>
      <div class="todo-meta-strip"><div class="todo-number-cell ${AppShell.statusClass(task.priorityLevel)}"><span>优先级</span><strong>${s(task.priority)}</strong><small>${s(task.deadline)}</small></div><div class="todo-number-cell"><span>执行人</span><strong>${s(task.assigneeName || "未派发")}</strong><small>${s(task.reviewerName || "待复核")}</small></div><div class="todo-number-cell warning"><span>动作权限</span><strong>${s(gate.actionLabel || task.actionType || "经营动作")}</strong><small>${s(taskBasis(task))}</small></div></div>
      <div class="todo-actions v106-minimal-actions">${actionButtons(task)}</div>
    </article>`;
  }
  async function refresh(message) { await AppApi.refreshTaskState(); notice = message; AppRouter.schedule("todo-refresh"); }
  function focusTask(taskId) { if (!taskId) return; requestAnimationFrame(() => { const card = document.querySelector(`[data-task-card="${CSS.escape(taskId)}"]`); if (!card) return; card.scrollIntoView({ behavior: "smooth", block: "center" }); card.style.boxShadow = "0 0 0 4px rgba(67, 56, 202, 0.18)"; setTimeout(() => { card.style.boxShadow = ""; }, 1800); }); }

  window.TodoPage = {
    route: "business-actions",
    title: "待办",
    async render(ctx) {
      const focusTaskId = ctx?.state?.focusTaskId || "";
      try { await AppApi.refreshTaskState(); } catch (error) { console.error("[todo] refresh task state failed", error); }
      const allTasks = AppTaskStore.listTasks();
      const active = AppTaskStore.listActiveTasks();
      const tasks = sortTasks(visibleTaskQueue(active));
      const counters = AppTaskStore.counters?.() || {};
      const user = AppApi.currentUser?.() || {};
      const empty = "当前账号没有需要立即处理的执行任务。候选任务、趋势信号和观察项进入日报/周报素材。";
      return `<section class="todo-toolbar"><div><p class="eyebrow">TASK CENTER · V12.6</p><h2>任务处理</h2><p>当前以 ${s(user.roleName || "默认账号")} 查看后端任务池。列表只按紧急程度和时间排序，完整SOP进入详情页。</p></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid todo-metrics">${metrics(allTasks, active, counters).map(([x,y,z]) => AppShell.metricCard(x,y,z)).join("")}</section><section class="page-section todo-list-section"><div class="section-header"><h3>执行队列</h3><span class="status-badge">${tasks.length} 个可执行任务</span></div><div class="todo-card-list">${tasks.length ? tasks.map((task, index) => row(task, index, focusTaskId)).join("") : `<div class="todo-empty">${s(empty)}</div>`}</div></section>`;
    },
    mount(ctx) {
      focusTask(ctx.state?.focusTaskId);
      ctx.delegate("[data-task-report]", "click", (_, node) => openTaskReport(node.dataset.taskReport));
      ctx.delegate("[data-assign]", "click", async (_, node) => { await AppApi.assignTodo(node.dataset.assign, { note: "派发任务给运营账号" }); await refresh("任务已派发。"); });
      ctx.delegate("[data-accept]", "click", async (_, node) => { await AppApi.acceptTodo(node.dataset.accept, { note: "运营已接收任务" }); await refresh("任务已接收，进入处理中。"); });
    },
  };
})();
