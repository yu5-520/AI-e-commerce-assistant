let dashboardLinkedRenderScheduled = false;

function isLinkedDashboardRoute() {
  const route = location.hash.replace("#", "") || "dashboard";
  return route === "dashboard" || document.querySelector('.nav a[data-route="dashboard"]')?.classList.contains("active");
}

function taskStore() {
  return window.OPERATION_TASK_STORE;
}

function activeDashboardTasks() {
  return taskStore()?.listActiveTasks?.() || [];
}

function dashboardMetrics(tasks) {
  return [
    { title: "紧急任务", value: tasks.filter((task) => task.priority === "高").length, desc: "优先处理" },
    { title: "到期任务", value: tasks.filter((task) => String(task.deadline || "").includes("今天")).length, desc: "有时间限制" },
    { title: "待确认", value: tasks.filter((task) => task.status === "待确认").length, desc: "确认前不执行" },
    { title: "任务来源", value: new Set(tasks.map((task) => task.sourceModule || task.source)).size, desc: "跨模块联动" },
  ];
}

function dashboardTimeBuckets(tasks) {
  const order = ["今天 18:00 前", "今天 20:00 前", "今天内", "明天前", "本周内", "每日"];
  const known = order
    .map((label) => ({ label, count: tasks.filter((task) => task.timeBucket === label || task.deadline === label).length }))
    .filter((item) => item.count > 0);
  const unknown = tasks.filter((task) => !order.includes(task.timeBucket) && !order.includes(task.deadline)).length;
  if (unknown) known.push({ label: "其他", count: unknown });
  return known;
}

function dashboardNowLabel(date = new Date()) {
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]} · ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")} 更新`;
}

function safeTags(task) {
  return Array.isArray(task.judgmentTags) ? task.judgmentTags : [];
}

function renderDashboardTimeSystem(tasks) {
  const buckets = dashboardTimeBuckets(tasks);
  return `<section class="dashboard-time-system">
    <div><strong>时间系统</strong><span>来自统一任务池，按截止时间自动分组</span></div>
    <div class="dashboard-time-chips">
      ${buckets.map((item) => `<span>${item.label}<strong>${item.count}</strong></span>`).join("")}
    </div>
  </section>`;
}

function renderDashboardJudgmentTags(task) {
  return `<div class="dashboard-judgment-tags">${safeTags(task).slice(0, 3).map((tag) => `<span>${tag}</span>`).join("")}</div>`;
}

function renderLinkedDashboardTask(task, index) {
  return `<article class="dashboard-task-card dashboard-linked-task dashboard-schedule-row">
    <div class="task-rank">${index + 1}</div>
    <div class="dashboard-schedule-time">
      <span>${task.priority || "中"}</span>
      <strong>${task.deadline || "本周内"}</strong>
    </div>
    <div class="dashboard-schedule-main">
      <div class="dashboard-linked-thumb">${task.imageLabel || "任"}</div>
      <div class="dashboard-schedule-copy">
        <div class="dashboard-schedule-title-line">
          <h3>${task.taskType || "经营任务"}</h3>
          <span>${task.taskSignal || task.status || "待处理"}</span>
        </div>
        <strong>${task.productShort || task.title || task.productId || "任务"}</strong>
        <small>${task.productId || "TASK"} · ${task.platform || "经营单元"} · ${task.store || "任务池"}</small>
      </div>
    </div>
    <div class="dashboard-schedule-source">
      <span>来源</span>
      <strong>${task.source || task.sourceModule || "系统"}</strong>
      <small>${task.sourceModule || "统一任务池"}</small>
    </div>
    <div class="dashboard-schedule-judgment">
      <span>判断</span>
      ${renderDashboardJudgmentTags(task)}
    </div>
    <div class="dashboard-linked-actions">
      <button type="button" data-dashboard-route="business-actions">进入待办</button>
      <button type="button" data-dashboard-route="${task.sourceRoute || "business-actions"}">查看来源</button>
      <button type="button" class="secondary" data-dashboard-route="${task.productRoute || task.sourceRoute || "business-products"}">对象</button>
      <button type="button" class="ghost" data-dashboard-complete="${task.id}">完成</button>
    </div>
  </article>`;
}

function renderLinkedDashboard() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || !isLinkedDashboardRoute()) return;
  const tasks = activeDashboardTasks();
  const topTasks = (taskStore()?.listDashboardTasks?.() || tasks).slice(0, 5);
  const metrics = dashboardMetrics(tasks);
  title.textContent = "总览";
  appView.innerHTML = `<section class="dashboard-status dashboard-linked-board">
    <div class="dashboard-status-main">
      <p class="eyebrow">COMMAND BOARD · V1.1 TASK FLOW</p>
      <h2>任务清单</h2>
      <p class="dashboard-time">${dashboardNowLabel()}</p>
    </div>
    <div class="dashboard-status-side">
      <span>统一任务池</span>
      <strong>动态联动</strong>
      <small>首页 · 待办 · 日志同步</small>
    </div>
  </section>
  <section class="kpi-grid dashboard-metrics dashboard-linked-metrics">
    ${metrics.map((item) => `<article class="card metric-card"><h3>${item.title}</h3><strong>${item.value}</strong><span class="card-desc">${item.desc}</span></article>`).join("")}
  </section>
  ${renderDashboardTimeSystem(tasks)}
  <section class="page-section dashboard-queue dashboard-linked-queue">
    <div class="section-header dashboard-linked-header">
      <div>
        <h3>处理顺序</h3>
        <span class="status-badge">任务池 / 时间 / 判断</span>
      </div>
      <button type="button" data-dashboard-route="business-actions">查看全部待办</button>
    </div>
    <section class="dashboard-task-list dashboard-schedule-list">
      ${topTasks.length ? topTasks.map(renderLinkedDashboardTask).join("") : `<article class="dashboard-empty">当前没有待处理任务，已完成记录可在日志中查看。</article>`}
    </section>
  </section>`;
  bindLinkedDashboardButtons();
}

function bindLinkedDashboardButtons() {
  document.querySelectorAll("[data-dashboard-route]").forEach((button) => {
    button.addEventListener("click", () => {
      location.hash = button.dataset.dashboardRoute;
    });
  });
  document.querySelectorAll("[data-dashboard-complete]").forEach((button) => {
    button.addEventListener("click", () => {
      taskStore()?.completeTask?.(button.dataset.dashboardComplete);
      renderLinkedDashboard();
    });
  });
}

function scheduleLinkedDashboardPatch() {
  if (dashboardLinkedRenderScheduled) return;
  dashboardLinkedRenderScheduled = true;
  setTimeout(() => {
    dashboardLinkedRenderScheduled = false;
    if (!isLinkedDashboardRoute()) return;
    if (document.querySelector(".dashboard-linked-board")) return;
    renderLinkedDashboard();
  }, 0);
}

const dashboardPatchObserver = new MutationObserver(() => {
  if (!isLinkedDashboardRoute()) return;
  if (document.querySelector(".dashboard-linked-board")) return;
  scheduleLinkedDashboardPatch();
});

dashboardPatchObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("operation-task-store-change", () => {
  if (isLinkedDashboardRoute()) renderLinkedDashboard();
});
window.addEventListener("hashchange", () => setTimeout(renderLinkedDashboard, 0));
window.addEventListener("load", () => setTimeout(renderLinkedDashboard, 0));
setTimeout(renderLinkedDashboard, 0);
setTimeout(renderLinkedDashboard, 250);
setTimeout(renderLinkedDashboard, 1000);
