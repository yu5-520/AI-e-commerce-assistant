(function () {
  let notice = "";
  const s = (value) => AppShell.escape(value);

  function row(task, index, focusTaskId = "") {
    const focused = focusTaskId && task.id === focusTaskId;
    const workflow = task.workflowStatus || task.status || "待派发";
    return `<article class="todo-card ${focused ? "focused-task" : ""}" data-task-card="${s(task.id)}"><div class="todo-rank ${AppShell.statusClass(task.priorityLevel)}">${index + 1}</div><div class="todo-title-cell"><div class="todo-thumb">${s(task.imageLabel || "任")}</div><div class="todo-title-block"><strong>${s(task.title || task.productTitle)}</strong><small>${s(task.productId || task.id)} · ${s(task.platform || "经营单元")} · ${s(task.store || "任务池")}</small><span>来源：${s(task.source || task.sourceModule)} · 截止：${s(task.deadline)}</span></div></div><div class="todo-task-block"><span>任务</span><strong>${s(task.task || task.taskType || "处理经营任务")}</strong><small>${s(task.reason || "由服务端任务池同步生成。")}</small></div><div class="todo-meta-strip"><div class="todo-number-cell ${AppShell.statusClass(task.priorityLevel)}"><span>优先级</span><strong>${s(task.priority)}</strong><small>${s(task.deadline)}</small></div><div class="todo-number-cell"><span>执行人</span><strong>${s(task.assigneeName || "未派发")}</strong><small>${s(task.assignedByName || "待总管拆分")}</small></div><div class="todo-number-cell warning"><span>状态</span><strong>${s(workflow)}</strong><small>${s(task.reviewerName || "待复核人")}</small></div></div><div class="todo-actions"><button type="button" data-task-report="${s(task.id)}">详情报告</button><button type="button" data-assign="${s(task.id)}">派发给运营</button><button type="button" data-submit="${s(task.id)}">运营提交</button><button type="button" class="primary" data-review="${s(task.id)}:approve">复核通过</button><button type="button" data-review="${s(task.id)}:return">退回</button><button type="button" data-pin="${s(task.id)}">置顶</button><button type="button" data-move="${s(task.id)}:up">上移</button><button type="button" data-move="${s(task.id)}:down">下移</button><button type="button" data-go="${s(task.sourceRoute || "dashboard")}">来源</button></div></article>`;
  }

  function metrics(allTasks, activeTasks) {
    return [
      ["待派发", activeTasks.filter((t) => !t.assigneeId).length, "老板 / 总管处理"],
      ["处理中", activeTasks.filter((t) => t.status === "处理中").length, "运营执行"],
      ["待复核", activeTasks.filter((t) => t.status === "待复核").length, "总管复核"],
      ["已完成", allTasks.filter((t) => t.status === "已完成").length, "进入日志追溯"],
    ];
  }

  async function refresh(message) {
    await AppApi.refreshTaskState();
    notice = message;
    AppRouter.schedule("todo-refresh");
  }

  function focusTask(taskId) {
    if (!taskId) return;
    requestAnimationFrame(() => {
      const card = document.querySelector(`[data-task-card="${CSS.escape(taskId)}"]`);
      if (!card) return;
      card.scrollIntoView({ behavior: "smooth", block: "center" });
      card.style.boxShadow = "0 0 0 4px rgba(67, 56, 202, 0.18)";
      setTimeout(() => { card.style.boxShadow = ""; }, 1800);
    });
  }

  window.TodoPage = {
    route: "business-actions",
    title: "待办",
    render(ctx) {
      const focusTaskId = ctx?.state?.focusTaskId || "";
      const allTasks = AppTaskStore.listTasks();
      const tasks = AppTaskStore.listActiveTasks();
      return `<section class="todo-toolbar"><div><p class="eyebrow">TASK CENTER · V2 COLLAB</p><h2>统一任务池</h2><p>任务现在支持派发、运营提交和总管复核。完成后从待办消失，只保留日志复盘。</p></div><div class="todo-filter-row"><button type="button" data-reset>重置演示</button></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid todo-metrics">${metrics(allTasks, tasks).map(([a,b,c]) => AppShell.metricCard(a,b,c)).join("")}</section><section class="page-section todo-list-section"><div class="section-header"><h3>执行队列</h3><span class="status-badge">${tasks.length} 个待办</span></div><div class="todo-card-list">${tasks.length ? tasks.map((task, index) => row(task, index, focusTaskId)).join("") : `<div class="todo-empty">当前没有待办任务，已完成任务请到日志复盘。</div>`}</div></section>`;
    },
    mount(ctx) {
      focusTask(ctx.state?.focusTaskId);
      ctx.delegate("[data-task-report]", "click", (_, node) => AppTaskActions.openTaskReport(node.dataset.taskReport));
      ctx.delegate("[data-assign]", "click", async (_, node) => {
        notice = "任务派发中...";
        AppRouter.schedule("todo-assign-start");
        await AppApi.assignTodo(node.dataset.assign, { note: "店群总管拆分任务给运营账号" });
        await refresh("任务已派发给运营，等待处理提交。");
      });
      ctx.delegate("[data-submit]", "click", async (_, node) => {
        notice = "运营提交中...";
        AppRouter.schedule("todo-submit-start");
        await AppApi.submitTodo(node.dataset.submit, { note: "运营已处理，提交店群总管复核。" });
        await refresh("任务已提交复核。");
      });
      ctx.delegate("[data-review]", "click", async (_, node) => {
        const [id, decision] = node.dataset.review.split(":");
        notice = "复核处理中...";
        AppRouter.schedule("todo-review-start");
        await AppApi.reviewTodo(id, { decision, note: decision === "approve" ? "复核通过，归档。" : "退回运营补充处理。" });
        await refresh(decision === "approve" ? "复核通过，任务已归档。" : "任务已退回运营处理。");
      });
      ctx.delegate("[data-pin]", "click", async (_, node) => { await AppApi.pinTodo(node.dataset.pin); await refresh("任务已置顶。"); });
      ctx.delegate("[data-move]", "click", async (_, node) => { const [id, direction] = node.dataset.move.split(":"); const moved = await AppApi.reorderTodo(id, direction); await refresh(moved ? "任务顺序已调整。" : "当前任务已经在边界位置。"); });
      ctx.delegate("[data-go]", "click", (_, node) => AppRouter.navigate(node.dataset.go));
      ctx.delegate("[data-reset]", "click", async () => { await AppApi.resetTodo(); await refresh("服务端演示任务池已重置。"); });
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();
