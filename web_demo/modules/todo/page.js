(function () {
  let notice = "";
  const s = (value) => AppShell.escape(value ?? "");

  function hasAction(task, action) { return (task.availableActions || []).includes(action); }
  function queueName(task) {
    const map = { urgent_execution: "紧急", today_execution: "今日", daily_operating_task: "今日", weekly_review_task: "复盘", candidate_only: "候选", report_seed_only: "素材" };
    return map[task.queueType] || "执行";
  }
  function actionDecision(task) {
    const gate = task.actionAuthorization || task.v127ActionGate || task.v126ActionGate || {};
    const map = { auto_execute: "运营执行", manager_approval_required: "主管审批", owner_approval_required: "老板确认" };
    return map[gate.decision] || (task.taskLayer === "manager_approval" ? "主管审批" : task.taskLayer === "operator_execution" ? "运营执行" : "任务");
  }
  function visibleTaskQueue(tasks) {
    return tasks.filter((task) => !["backend_tag", "store_product_tag", "observe_candidate", "candidate_only", "report_seed_only", "merged_duplicate"].includes(task.queueType) && task.displayState !== "backend_only");
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
  function reasonFamily(task) {
    const text = [task.riskDomain, task.reason, task.task, task.actionType, (task.taskDetailReport || {}).warningSummary].join(" ");
    if (text.includes("库存") || text.includes("补货") || text.includes("可售")) return "库存警告";
    if (text.includes("点击") || text.includes("素材") || text.includes("主图")) return "点击素材";
    if (text.includes("转化") || text.includes("详情") || text.includes("评价") || text.includes("客服")) return "转化承接";
    if (text.includes("广告") || text.includes("预算") || text.includes("投放") || text.includes("人群") || text.includes("关键词")) return "投放效率";
    if (text.includes("退款") || text.includes("售后")) return "售后退款";
    return task.riskDomain || "经营判断";
  }
  function lifecycleLabel(task) {
    const lifecycle = task.taskLifecycle || {};
    return lifecycle.stageLabel || lifecycle.stage || "生成任务";
  }
  function lifecycleNext(task) {
    return (task.taskLifecycle || {}).nextExpected || task.displayStatus || task.workflowStatus || task.status || "待处理";
  }
  function metrics(activeTasks, visibleTasks) {
    return [["执行任务", visibleTasks.length, "后端队列"], ["紧急/高", visibleTasks.filter((t) => t.priority === "高").length, "优先处理"], ["主管确认", visibleTasks.filter((t) => t.taskLayer === "manager_approval").length, "权限闸门"], ["处理中", activeTasks.filter((t) => t.status === "处理中").length, "执行中"], ["待复盘", activeTasks.filter((t) => ["已完成", "已通过", "已写入复盘"].includes(t.status)).length, "周期回看"]];
  }
  function openTaskReport(taskId) { AppRouter.navigate("task-report", { taskId }); }
  function actionButtons(task) {
    const id = s(task.id);
    const buttons = [`<button type="button" data-task-report="${id}">详情</button>`];
    if (hasAction(task, "accept")) buttons.unshift(`<button type="button" class="primary" data-accept="${id}">接收</button>`);
    if (hasAction(task, "submit")) buttons.unshift(`<button type="button" class="primary" data-task-report="${id}">提交</button>`);
    if (hasAction(task, "review")) buttons.unshift(`<button type="button" class="primary" data-task-report="${id}">复核</button>`);
    if (hasAction(task, "write_recap")) buttons.unshift(`<button type="button" class="primary" data-task-report="${id}">复盘</button>`);
    return buttons.join("");
  }
  function row(task, index, focusTaskId = "") {
    const focused = focusTaskId && task.id === focusTaskId;
    const gate = task.actionAuthorization || task.v127ActionGate || task.v126ActionGate || {};
    const workflow = task.displayStatus || task.workflowStatus || task.status || "待处理";
    const batch = task.batchTask ? `<em>${s(task.affectedProductCount)}品</em>` : "";
    const lifecycle = lifecycleLabel(task);
    return `<article class="todo-queue-row ${focused ? "focused-task" : ""}" data-task-card="${s(task.id)}">
      <div class="todo-queue-rank">${index + 1}</div>
      <div class="todo-queue-main"><strong>${s(task.title || task.productTitle)}</strong><span>${s(task.store || task.storeName || "任务池")} · ${s(task.platform || "经营单元")} · ${s(gate.actionLabel || task.actionType || reasonFamily(task))}</span></div>
      <div class="todo-queue-badges"><em>${s(task.priority || "中")}</em><em>${s(task.deadline || task.timeBucket || "今日内")}</em><em>${s(queueName(task))}</em><em>${s(lifecycle)}</em>${batch}</div>
      <div class="todo-queue-status"><strong>${s(actionDecision(task))}</strong><span>${s(workflow)} · ${s(lifecycleNext(task))}</span></div>
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
      const active = AppTaskStore.listActiveTasks();
      const tasks = sortTasks(visibleTaskQueue(active));
      const user = AppApi.currentUser?.() || {};
      const empty = "当前账号没有需要立即处理的执行任务。候选任务、趋势信号和观察项进入日报/周报素材。";
      return `<section class="todo-toolbar"><div><p class="eyebrow">TASK CENTER · V12.8.1</p><h2>任务处理</h2><p>当前以 ${s(user.roleName || "默认账号")} 查看后端真实任务队列。前端不再二次聚合；接收、提交、复核、复盘全部围绕同一个 task_id 流转。</p></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid todo-metrics">${metrics(active, tasks).map(([x,y,z]) => AppShell.metricCard(x,y,z)).join("")}</section><section class="page-section todo-list-section"><div class="section-header"><h3>执行队列</h3><span class="status-badge">${tasks.length} 个队列任务</span></div><div class="todo-queue-list">${tasks.length ? tasks.map((task, index) => row(task, index, focusTaskId)).join("") : `<div class="todo-empty">${s(empty)}</div>`}</div></section>`;
    },
    mount(ctx) {
      focusTask(ctx.state?.focusTaskId);
      ctx.delegate("[data-task-report]", "click", (_, node) => openTaskReport(node.dataset.taskReport));
      ctx.delegate("[data-accept]", "click", async (_, node) => { await AppApi.acceptTodo(node.dataset.accept, { note: "运营已接收任务" }); await refresh("任务已接收，进入处理中。"); });
    },
  };
})();
