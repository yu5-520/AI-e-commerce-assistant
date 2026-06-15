let activeTodoId = null;
let todoNotice = "";
let openTodoFilter = null;
let todoRenderScheduled = false;
const todoFilters = {
  source: "全部来源",
  status: "全部状态",
  priority: "全部优先级",
  search: "",
};

function taskStore() {
  return window.OPERATION_TASK_STORE;
}

function isTodoRoute() {
  return location.hash.replace("#", "") === "business-actions" || document.querySelector('.nav a[data-route="business-actions"]')?.classList.contains("active");
}

function todoStatusClass(level) {
  return level === "danger" ? "danger" : level === "warning" ? "warning" : "good";
}

function allTodoTasks() {
  return taskStore()?.listTasks?.() || [];
}

function currentTodoStatus(task) {
  return task.status || "待确认";
}

function todoNoticeMarkup() {
  if (!todoNotice) return "";
  return `<section class="todo-notice"><strong>操作结果</strong><span>${todoNotice}</span></section>`;
}

function todoFilterOptions(type) {
  const tasks = allTodoTasks();
  if (type === "source") return ["全部来源", ...new Set(tasks.map((item) => item.source || item.sourceModule || "系统"))];
  if (type === "status") return ["全部状态", ...new Set(["待确认", "处理中", "已完成", "已拒绝", ...tasks.map((item) => currentTodoStatus(item))])];
  return ["全部优先级", "高", "中", "低"];
}

function renderTodoFilter(type, label) {
  const value = todoFilters[type];
  const isOpen = openTodoFilter === type;
  return `<div class="todo-filter-menu ${isOpen ? "open" : ""}">
    <button type="button" data-todo-filter-toggle="${type}">${label}：${value} <span>⌄</span></button>
    <div class="todo-filter-options">
      ${todoFilterOptions(type).map((option) => `<button type="button" class="${option === value ? "selected" : ""}" data-todo-filter-value="${type}:${option}">${option}</button>`).join("")}
    </div>
  </div>`;
}

function todoMatchesFilters(task) {
  const source = task.source || task.sourceModule || "系统";
  if (todoFilters.source !== "全部来源" && source !== todoFilters.source) return false;
  if (todoFilters.status !== "全部状态" && currentTodoStatus(task) !== todoFilters.status) return false;
  if (todoFilters.priority !== "全部优先级" && task.priority !== todoFilters.priority) return false;
  const keyword = todoFilters.search.trim().toLowerCase();
  if (!keyword) return true;
  return [task.id, task.productId, task.title, task.productTitle, task.platform, task.store, source, task.taskType, task.taskSignal, task.task, task.reason, task.deadline, currentTodoStatus(task)]
    .join(" ")
    .toLowerCase()
    .includes(keyword);
}

function sortedTodoTasks() {
  return allTodoTasks().filter(todoMatchesFilters);
}

function todoMetrics() {
  const tasks = allTodoTasks();
  return [
    { label: "紧急任务", value: tasks.filter((item) => item.priority === "高" && currentTodoStatus(item) !== "已完成").length, desc: "优先处理" },
    { label: "今日到期", value: tasks.filter((item) => String(item.deadline || "").includes("今天") && currentTodoStatus(item) !== "已完成").length, desc: "有明确时间限制" },
    { label: "待确认", value: tasks.filter((item) => currentTodoStatus(item) === "待确认").length, desc: "需要人工判断" },
    { label: "已完成", value: tasks.filter((item) => currentTodoStatus(item) === "已完成").length, desc: "进入日志追溯" },
  ];
}

function todoFilterSummary(count) {
  const active = [
    todoFilters.source !== "全部来源" ? todoFilters.source : null,
    todoFilters.status !== "全部状态" ? todoFilters.status : null,
    todoFilters.priority !== "全部优先级" ? todoFilters.priority : null,
    todoFilters.search.trim() ? `搜索：${todoFilters.search.trim()}` : null,
  ].filter(Boolean);
  return active.length ? `${count} 个任务 · ${active.join(" / ")}` : `${count} 个任务`;
}

function renderTodoActions(task) {
  return `<button type="button" class="primary" data-todo-complete="${task.id}">完成</button>
    <button type="button" data-todo-pin="${task.id}">置顶</button>
    <button type="button" data-todo-reorder="${task.id}:up">上移</button>
    <button type="button" data-todo-reorder="${task.id}:down">下移</button>
    <button type="button" data-todo-source="${task.sourceRoute || "dashboard"}">来源</button>
    <button type="button" data-todo-detail="${task.id}">详情</button>`;
}

function renderTodoCard(task, index) {
  const status = currentTodoStatus(task);
  return `<article class="todo-card">
    <div class="todo-rank ${todoStatusClass(task.priorityLevel)}">${index + 1}</div>
    <div class="todo-title-cell">
      <div class="todo-thumb">${task.imageLabel || "任"}</div>
      <div class="todo-title-block">
        <strong>${task.title || task.productTitle || task.task || "经营任务"}</strong>
        <small>${task.productId || task.id} · ${task.platform || "经营单元"} · ${task.store || "任务池"}</small>
        <span>来源：${task.source || task.sourceModule || "系统"} · 截止：${task.deadline || "本周内"}</span>
      </div>
    </div>
    <div class="todo-task-block">
      <span>任务</span>
      <strong>${task.task || task.taskType || task.taskSignal || "处理经营任务"}</strong>
      <small>${task.reason || "由统一任务池同步生成。"}</small>
    </div>
    <div class="todo-meta-strip">
      <div class="todo-number-cell ${todoStatusClass(task.priorityLevel)}"><span>优先级</span><strong>${task.priority || "中"}</strong><small>${task.deadline || "本周内"}</small></div>
      <div class="todo-number-cell"><span>来源</span><strong>${task.source || task.sourceModule || "系统"}</strong><small>统一任务池</small></div>
      <div class="todo-number-cell ${status === "已完成" ? "good" : status === "已拒绝" ? "danger" : "warning"}"><span>状态</span><strong>${status}</strong><small>人工处理</small></div>
    </div>
    <div class="todo-actions">
      ${renderTodoActions(task)}
    </div>
  </article>`;
}

function renderTodoManager() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || !isTodoRoute()) return;
  const tasks = sortedTodoTasks();
  activeTodoId = null;
  title.textContent = "待办";
  appView.innerHTML = `<section class="todo-toolbar">
    <div>
      <p class="eyebrow">TASK CENTER · V1.1</p>
      <h2>统一任务池</h2>
      <p>商品、竞品、上新、流量、报表和首页共用同一套任务状态；排序、完成和日志同步刷新。</p>
    </div>
    <div class="todo-filter-row">
      ${renderTodoFilter("source", "来源")}
      ${renderTodoFilter("status", "状态")}
      ${renderTodoFilter("priority", "优先级")}
      <label class="todo-search"><input type="search" value="${todoFilters.search}" placeholder="搜索任务 / 商品" data-todo-search /></label>
      <button type="button" data-todo-reset>重置演示</button>
    </div>
  </section>
  ${todoNoticeMarkup()}
  <section class="kpi-grid todo-metrics">
    ${todoMetrics().map((item) => `<article class="card todo-metric-card"><h3>${item.label}</h3><strong>${item.value}</strong><span class="card-desc">${item.desc}</span></article>`).join("")}
  </section>
  <section class="page-section todo-list-section">
    <div class="section-header">
      <h3>执行队列</h3>
      <span class="status-badge">${todoFilterSummary(tasks.length)}</span>
    </div>
    <div class="todo-card-list">
      ${tasks.length ? tasks.map(renderTodoCard).join("") : `<div class="todo-empty">当前筛选条件下没有待办任务。</div>`}
    </div>
  </section>`;
  bindTodoButtons();
}

function renderTodoDetail(taskId) {
  const task = allTodoTasks().find((item) => item.id === taskId);
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!task || !appView || !title) return;
  activeTodoId = taskId;
  openTodoFilter = null;
  const status = currentTodoStatus(task);
  title.textContent = "待办详情";
  appView.innerHTML = `<section class="todo-detail-hero">
    <div class="todo-detail-main">
      <div class="todo-thumb large">${task.imageLabel || "任"}</div>
      <div>
        <p class="eyebrow">TASK DETAIL</p>
        <h2>${task.title || task.productTitle || task.task}</h2>
        <p>${task.platform || "经营单元"} · ${task.store || "任务池"} · ${task.source || task.sourceModule || "系统"}</p>
        <span>${task.link || "统一任务池"}</span>
      </div>
    </div>
    <div class="todo-detail-actions">
      <button type="button" data-todo-back>返回待办</button>
      <button type="button" data-todo-source="${task.sourceRoute || "dashboard"}">查看来源</button>
      <button type="button" data-todo-pin="${task.id}">置顶</button>
      <button type="button" data-todo-complete="${task.id}">完成</button>
    </div>
  </section>
  ${todoNoticeMarkup()}
  <section class="kpi-grid todo-detail-metrics">
    <article class="card"><h3>优先级</h3><strong class="metric-${todoStatusClass(task.priorityLevel)}">${task.priority || "中"}</strong><span class="card-desc">${task.deadline || "本周内"}</span></article>
    <article class="card"><h3>来源</h3><strong>${task.source || task.sourceModule || "系统"}</strong><span class="card-desc">${task.productId || task.id}</span></article>
    <article class="card"><h3>状态</h3><strong>${status}</strong><span class="card-desc">人工处理</span></article>
    <article class="card"><h3>排序</h3><strong>${task.manualOrder || "-"}</strong><span class="card-desc">可人工调整</span></article>
  </section>
  <section class="page-section todo-detail-section">
    <div class="section-header"><h3>任务动作</h3><span class="status-badge">${task.deadline || "本周内"}</span></div>
    <p>${task.task || task.taskType || task.taskSignal || "处理经营任务"}</p>
  </section>
  <section class="page-section todo-detail-section">
    <div class="section-header"><h3>生成原因</h3><span class="status-badge pending">${task.source || task.sourceModule || "系统"}</span></div>
    <p>${task.reason || "由统一任务池同步生成。"}</p>
  </section>`;
  bindTodoButtons();
}

function bindTodoButtons() {
  document.querySelectorAll("[data-todo-filter-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      openTodoFilter = openTodoFilter === button.dataset.todoFilterToggle ? null : button.dataset.todoFilterToggle;
      renderTodoManager();
    });
  });
  document.querySelectorAll("[data-todo-filter-value]").forEach((button) => {
    button.addEventListener("click", () => {
      const [type, value] = button.dataset.todoFilterValue.split(":");
      todoFilters[type] = value;
      openTodoFilter = null;
      todoNotice = "";
      renderTodoManager();
    });
  });
  document.querySelector("[data-todo-search]")?.addEventListener("input", (event) => {
    todoFilters.search = event.target.value;
    renderTodoManager();
    document.querySelector("[data-todo-search]")?.focus();
  });
  document.querySelectorAll("[data-todo-detail]").forEach((button) => {
    button.addEventListener("click", () => {
      todoNotice = "";
      renderTodoDetail(button.dataset.todoDetail);
    });
  });
  document.querySelectorAll("[data-todo-back]").forEach((button) => {
    button.addEventListener("click", () => {
      activeTodoId = null;
      todoNotice = "";
      renderTodoManager();
    });
  });
  document.querySelectorAll("[data-todo-source]").forEach((button) => {
    button.addEventListener("click", () => {
      location.hash = button.dataset.todoSource;
    });
  });
  document.querySelectorAll("[data-todo-complete]").forEach((button) => {
    button.addEventListener("click", () => {
      const task = taskStore()?.completeTask?.(button.dataset.todoComplete);
      todoNotice = `${task?.title || "任务"}已完成，并写入日志。`;
      if (activeTodoId) renderTodoDetail(activeTodoId);
      else renderTodoManager();
    });
  });
  document.querySelectorAll("[data-todo-pin]").forEach((button) => {
    button.addEventListener("click", () => {
      const task = taskStore()?.pinTask?.(button.dataset.todoPin);
      todoNotice = `${task?.title || "任务"}已置顶。`;
      if (activeTodoId) renderTodoDetail(activeTodoId);
      else renderTodoManager();
    });
  });
  document.querySelectorAll("[data-todo-reorder]").forEach((button) => {
    button.addEventListener("click", () => {
      const [taskId, direction] = button.dataset.todoReorder.split(":");
      const task = taskStore()?.reorderTask?.(taskId, direction);
      todoNotice = task ? "任务顺序已调整，并同步首页。" : "当前任务已经在边界位置。";
      renderTodoManager();
    });
  });
  document.querySelector("[data-todo-reset]")?.addEventListener("click", () => {
    taskStore()?.resetDemoData?.();
    todoNotice = "演示任务池已重置。";
    renderTodoManager();
  });
}

function scheduleTodoPatch() {
  if (todoRenderScheduled) return;
  todoRenderScheduled = true;
  setTimeout(() => {
    todoRenderScheduled = false;
    if (!isTodoRoute()) return;
    if (activeTodoId) renderTodoDetail(activeTodoId);
    else renderTodoManager();
  }, 0);
}

const todoObserver = new MutationObserver(() => {
  if (!isTodoRoute()) return;
  if (document.querySelector(".todo-toolbar") || document.querySelector(".todo-detail-hero")) return;
  scheduleTodoPatch();
});

todoObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("operation-task-store-change", () => {
  if (isTodoRoute()) scheduleTodoPatch();
});
window.addEventListener("hashchange", () => {
  activeTodoId = null;
  todoNotice = "";
  openTodoFilter = null;
  scheduleTodoPatch();
});
window.addEventListener("load", scheduleTodoPatch);
scheduleTodoPatch();
