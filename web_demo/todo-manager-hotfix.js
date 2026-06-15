const todoManagerPayload = {
  tasks: [
    {
      id: "A001",
      priority: "高",
      priorityLevel: "danger",
      deadline: "今天 18:00 前",
      deadlineRank: 1,
      source: "流量触发",
      moduleRoute: "business-traffic",
      productId: "P002",
      imageLabel: "架",
      title: "厨房置物架免打孔收纳架壁挂多层家用置物架",
      platform: "拼多多",
      store: "家居百货店",
      link: "https://shop.example.com/products/P002",
      task: "先查售后，不继续放大推广预算",
      reason: "搜索推广 ROI 1.1，退款率 6.8%，安装和尺寸咨询偏高。",
      status: "待确认",
      actions: ["进入售后归因", "继续观察", "拒绝"],
    },
    {
      id: "A002",
      priority: "高",
      priorityLevel: "danger",
      deadline: "今天内",
      deadlineRank: 2,
      source: "AI 自动判定",
      moduleRoute: "business-products",
      productId: "P003",
      imageLabel: "垫",
      title: "护腰坐垫久坐办公室靠垫人体工学支撑款",
      platform: "抖音小店",
      store: "家居好物号",
      link: "https://shop.example.com/products/P003",
      task: "暂停投放并复查材质、支撑感和客服承诺",
      reason: "售后敏感未解决，推荐流量 ROI 0.9，退款率 8.4%。",
      status: "待确认",
      actions: ["暂停投放", "进入商品复查", "拒绝"],
    },
    {
      id: "A003",
      priority: "高",
      priorityLevel: "danger",
      deadline: "今天 20:00 前",
      deadlineRank: 3,
      source: "上新触发",
      moduleRoute: "business-listing",
      productId: "P001",
      imageLabel: "伞",
      title: "遮阳伞户外便携防晒防紫外线晴雨两用",
      platform: "淘宝",
      store: "家居生活主店",
      link: "https://shop.example.com/products/P001",
      task: "确认平台券活动价和利润安全线",
      reason: "活动测试进入确认期，需确认 ROI、退款率和库存承接。",
      status: "待确认",
      actions: ["确认测试", "推迟测试", "取消测试"],
    },
    {
      id: "A004",
      priority: "中",
      priorityLevel: "warning",
      deadline: "明天 12:00 前",
      deadlineRank: 4,
      source: "商品触发",
      moduleRoute: "business-products",
      productId: "P004",
      imageLabel: "盒",
      title: "透明收纳盒衣柜整理箱家用大容量防尘款",
      platform: "淘宝",
      store: "家居生活主店",
      link: "https://shop.example.com/products/P004",
      task: "确认补货周期，再决定是否继续活动流量",
      reason: "库存 46，接近安全线；活动流量 ROI 1.3，可谨慎放量。",
      status: "待确认",
      actions: ["确认处理", "继续观察", "拒绝"],
    },
    {
      id: "A005",
      priority: "中",
      priorityLevel: "warning",
      deadline: "明天 18:00 前",
      deadlineRank: 5,
      source: "竞品触发",
      moduleRoute: "business-competitors",
      productId: "P002",
      imageLabel: "装",
      title: "厨房置物架：新增安装说明图 + 尺寸参照图版本",
      platform: "拼多多",
      store: "家居百货店",
      link: "https://shop.example.com/products/P002",
      task: "生成详情页测试版本并加入上新测试",
      reason: "竞品差评集中在安装困难 / 尺寸不符，可转为测试动作。",
      status: "待确认",
      actions: ["生成上新版本", "加入观察", "拒绝"],
    },
    {
      id: "A006",
      priority: "中",
      priorityLevel: "warning",
      deadline: "3 天后复盘",
      deadlineRank: 6,
      source: "上新触发",
      moduleRoute: "business-listing",
      productId: "P004",
      imageLabel: "盒",
      title: "透明收纳盒衣柜整理箱家用大容量防尘款",
      platform: "淘宝",
      store: "家居生活主店",
      link: "https://shop.example.com/products/P004",
      task: "复盘 SKU 基础款 / 加厚款 / 组合款测试",
      reason: "组合款会占用库存，需观察转化率和库存承接。",
      status: "处理中",
      actions: ["进入复盘", "继续观察", "取消测试"],
    },
    {
      id: "A007",
      priority: "低",
      priorityLevel: "good",
      deadline: "本周内",
      deadlineRank: 7,
      source: "报表触发",
      moduleRoute: "data-check",
      productId: "R001",
      imageLabel: "表",
      title: "退款报表与商品报表同步检查",
      platform: "ERP / CRM",
      store: "家居生活店铺组",
      link: "#data-check",
      task: "导入最新退款报表，生成本轮复盘摘要",
      reason: "流量测试和售后归因需要最新退款原因数据。",
      status: "待确认",
      actions: ["导入报表", "生成报告", "稍后处理"],
    },
    {
      id: "A008",
      priority: "低",
      priorityLevel: "good",
      deadline: "每天 09:00",
      deadlineRank: 8,
      source: "AI 自动判定",
      moduleRoute: "business-report",
      productId: "DAILY",
      imageLabel: "报",
      title: "生成经营日报和下一轮任务摘要",
      platform: "经营单元",
      store: "家居生活店铺组",
      link: "#business-report",
      task: "生成日报，沉淀商品、竞品、上新、流量任务结论",
      reason: "用于总览页任务摘要和明日复盘。",
      status: "待确认",
      actions: ["生成报告", "稍后处理", "拒绝"],
    },
  ],
};

let activeTodoId = null;
let todoNotice = "";
let openTodoFilter = null;
let todoRenderScheduled = false;
const todoState = {};
const todoFilters = {
  source: "全部来源",
  status: "全部状态",
  priority: "全部优先级",
  search: "",
};

function isTodoRoute() {
  return location.hash.replace("#", "") === "business-actions" || document.querySelector('.nav a[data-route="business-actions"]')?.classList.contains("active");
}

function todoStatusClass(level) {
  return level === "danger" ? "danger" : level === "warning" ? "warning" : "good";
}

function currentTodoStatus(task) {
  return todoState[task.id] || task.status;
}

function todoNoticeMarkup() {
  if (!todoNotice) return "";
  return `<section class="todo-notice"><strong>操作结果</strong><span>${todoNotice}</span></section>`;
}

function todoFilterOptions(type) {
  if (type === "source") return ["全部来源", ...new Set(todoManagerPayload.tasks.map((item) => item.source))];
  if (type === "status") return ["全部状态", "待确认", "处理中", "已确认", "已拒绝", "稍后处理"];
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
  if (todoFilters.source !== "全部来源" && task.source !== todoFilters.source) return false;
  if (todoFilters.status !== "全部状态" && currentTodoStatus(task) !== todoFilters.status) return false;
  if (todoFilters.priority !== "全部优先级" && task.priority !== todoFilters.priority) return false;
  const keyword = todoFilters.search.trim().toLowerCase();
  if (!keyword) return true;
  return [task.id, task.productId, task.title, task.platform, task.store, task.source, task.task, task.reason, task.deadline, currentTodoStatus(task)]
    .join(" ")
    .toLowerCase()
    .includes(keyword);
}

function sortedTodoTasks() {
  return todoManagerPayload.tasks
    .filter(todoMatchesFilters)
    .sort((a, b) => a.deadlineRank - b.deadlineRank);
}

function todoMetrics() {
  const tasks = todoManagerPayload.tasks;
  return [
    { label: "紧急任务", value: tasks.filter((item) => item.priority === "高" && currentTodoStatus(item) !== "已确认").length, desc: "优先处理" },
    { label: "今日到期", value: tasks.filter((item) => item.deadline.includes("今天") && currentTodoStatus(item) !== "已确认").length, desc: "有明确时间限制" },
    { label: "待确认", value: tasks.filter((item) => currentTodoStatus(item) === "待确认").length, desc: "需要人工判断" },
    { label: "AI 自动判定", value: tasks.filter((item) => item.source === "AI 自动判定").length, desc: "系统主动生成" },
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
  return task.actions
    .map((action, index) => `<button type="button" class="${index === 0 ? "primary" : ""}" data-todo-action="${task.id}:${action}">${action}</button>`)
    .join("");
}

function renderTodoCard(task, index) {
  const status = currentTodoStatus(task);
  return `<article class="todo-card">
    <div class="todo-rank ${todoStatusClass(task.priorityLevel)}">${index + 1}</div>
    <div class="todo-title-cell">
      <div class="todo-thumb">${task.imageLabel}</div>
      <div class="todo-title-block">
        <strong>${task.title}</strong>
        <small>${task.productId} · ${task.platform} · ${task.store}</small>
        <span>来源：${task.source} · 截止：${task.deadline}</span>
      </div>
    </div>
    <div class="todo-task-block">
      <span>任务</span>
      <strong>${task.task}</strong>
      <small>${task.reason}</small>
    </div>
    <div class="todo-meta-strip">
      <div class="todo-number-cell ${todoStatusClass(task.priorityLevel)}"><span>优先级</span><strong>${task.priority}</strong><small>${task.deadline}</small></div>
      <div class="todo-number-cell"><span>来源</span><strong>${task.source}</strong><small>模块回流</small></div>
      <div class="todo-number-cell ${status === "已确认" ? "good" : status === "已拒绝" ? "danger" : "warning"}"><span>状态</span><strong>${status}</strong><small>人工处理</small></div>
    </div>
    <div class="todo-actions">
      ${renderTodoActions(task)}
      <button type="button" data-todo-detail="${task.id}">详情</button>
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
      <p class="eyebrow">TASK CENTER</p>
      <h2>待办任务</h2>
      <p>集中排列商品、竞品、上新、流量、报表和 AI 自动判定产生的任务，并按时间限制和紧急程度排序。</p>
    </div>
    <div class="todo-filter-row">
      ${renderTodoFilter("source", "来源")}
      ${renderTodoFilter("status", "状态")}
      ${renderTodoFilter("priority", "优先级")}
      <label class="todo-search"><input type="search" value="${todoFilters.search}" placeholder="搜索任务 / 商品" data-todo-search /></label>
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
  const task = todoManagerPayload.tasks.find((item) => item.id === taskId);
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!task || !appView || !title) return;
  activeTodoId = taskId;
  openTodoFilter = null;
  const status = currentTodoStatus(task);
  title.textContent = "待办详情";
  appView.innerHTML = `<section class="todo-detail-hero">
    <div class="todo-detail-main">
      <div class="todo-thumb large">${task.imageLabel}</div>
      <div>
        <p class="eyebrow">TASK DETAIL</p>
        <h2>${task.title}</h2>
        <p>${task.platform} · ${task.store} · ${task.source}</p>
        <a href="${task.link}" target="_blank" rel="noreferrer">${task.link}</a>
      </div>
    </div>
    <div class="todo-detail-actions">
      <button type="button" data-todo-back>返回待办</button>
      <button type="button" data-todo-source="${task.moduleRoute}">查看来源</button>
      ${renderTodoActions(task)}
    </div>
  </section>
  ${todoNoticeMarkup()}
  <section class="kpi-grid todo-detail-metrics">
    <article class="card"><h3>优先级</h3><strong class="metric-${todoStatusClass(task.priorityLevel)}">${task.priority}</strong><span class="card-desc">${task.deadline}</span></article>
    <article class="card"><h3>来源</h3><strong>${task.source}</strong><span class="card-desc">${task.productId}</span></article>
    <article class="card"><h3>状态</h3><strong>${status}</strong><span class="card-desc">人工处理</span></article>
    <article class="card"><h3>排序</h3><strong>${task.deadlineRank}</strong><span class="card-desc">越小越优先</span></article>
  </section>
  <section class="page-section todo-detail-section">
    <div class="section-header"><h3>任务动作</h3><span class="status-badge">${task.deadline}</span></div>
    <p>${task.task}</p>
  </section>
  <section class="page-section todo-detail-section">
    <div class="section-header"><h3>生成原因</h3><span class="status-badge pending">${task.source}</span></div>
    <p>${task.reason}</p>
  </section>`;
  bindTodoButtons();
}

function applyTodoAction(taskId, action) {
  const task = todoManagerPayload.tasks.find((item) => item.id === taskId);
  if (!task) return;
  if (action === "拒绝" || action === "取消测试") todoState[taskId] = "已拒绝";
  else if (action === "稍后处理" || action === "继续观察" || action === "加入观察") todoState[taskId] = "处理中";
  else todoState[taskId] = "已确认";
  todoNotice = `${task.title}：${action}已记录。`;
  if (activeTodoId) renderTodoDetail(activeTodoId);
  else renderTodoManager();
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
  document.querySelectorAll("[data-todo-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const [taskId, action] = button.dataset.todoAction.split(":");
      applyTodoAction(taskId, action);
    });
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
window.addEventListener("hashchange", () => {
  activeTodoId = null;
  todoNotice = "";
  openTodoFilter = null;
  scheduleTodoPatch();
});
window.addEventListener("load", scheduleTodoPatch);
scheduleTodoPatch();
