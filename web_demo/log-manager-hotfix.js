let activeLogId = null;
let logNotice = "";
let openLogFilter = null;
let logRenderScheduled = false;
const logFilters = {
  type: "全部类型",
  source: "全部来源",
  status: "全部状态",
  search: "",
};

function taskStore() {
  return window.OPERATION_TASK_STORE;
}

function isLogRoute() {
  return location.hash.replace("#", "") === "business-report" || document.querySelector('.nav a[data-route="business-report"]')?.classList.contains("active");
}

function logLevelClass(level) {
  return level === "danger" ? "danger" : level === "warning" ? "warning" : "good";
}

function allLogs() {
  return taskStore()?.listLogs?.() || [];
}

function logNoticeMarkup() {
  if (!logNotice) return "";
  return `<section class="log-notice"><strong>操作结果</strong><span>${logNotice}</span></section>`;
}

function logFilterOptions(type) {
  const logs = allLogs();
  if (type === "type") return ["全部类型", ...new Set(logs.map((item) => item.type || "任务记录"))];
  if (type === "source") return ["全部来源", ...new Set(logs.map((item) => item.source || "系统"))];
  return ["全部状态", ...new Set(logs.map((item) => item.status || "已记录"))];
}

function renderLogFilter(type, label) {
  const value = logFilters[type];
  const isOpen = openLogFilter === type;
  return `<div class="log-filter-menu ${isOpen ? "open" : ""}">
    <button type="button" data-log-filter-toggle="${type}">${label}：${value} <span>⌄</span></button>
    <div class="log-filter-options">
      ${logFilterOptions(type).map((option) => `<button type="button" class="${option === value ? "selected" : ""}" data-log-filter-value="${type}:${option}">${option}</button>`).join("")}
    </div>
  </div>`;
}

function logMatchesFilters(log) {
  if (logFilters.type !== "全部类型" && log.type !== logFilters.type) return false;
  if (logFilters.source !== "全部来源" && log.source !== logFilters.source) return false;
  if (logFilters.status !== "全部状态" && log.status !== logFilters.status) return false;
  const keyword = logFilters.search.trim().toLowerCase();
  if (!keyword) return true;
  return [log.id, log.time, log.type, log.source, log.status, log.title, log.platform, log.store, log.productId, log.action, log.reason, log.result]
    .join(" ")
    .toLowerCase()
    .includes(keyword);
}

function filteredLogs() {
  return allLogs().filter(logMatchesFilters);
}

function logMetrics() {
  const logs = allLogs();
  return [
    { label: "今日记录", value: logs.length, desc: "任务池流水" },
    { label: "任务创建", value: logs.filter((item) => item.type === "任务创建" || item.type === "任务进入池").length, desc: "模块进入待办" },
    { label: "任务完成", value: logs.filter((item) => item.type === "任务完成").length, desc: "闭环记录" },
    { label: "排序动作", value: logs.filter((item) => item.type === "任务排序" || item.type === "任务置顶").length, desc: "人工调度" },
  ];
}

function logFilterSummary(count) {
  const active = [
    logFilters.type !== "全部类型" ? logFilters.type : null,
    logFilters.source !== "全部来源" ? logFilters.source : null,
    logFilters.status !== "全部状态" ? logFilters.status : null,
    logFilters.search.trim() ? `搜索：${logFilters.search.trim()}` : null,
  ].filter(Boolean);
  return active.length ? `${count} 条日志 · ${active.join(" / ")}` : `${count} 条日志`;
}

function renderLogRow(log) {
  return `<article class="log-row">
    <div class="log-time-block ${logLevelClass(log.level)}">
      <strong>${log.time || "--:--"}</strong>
      <span>${log.type || "任务记录"}</span>
    </div>
    <div class="log-title-cell">
      <div class="log-thumb">${log.imageLabel || "记"}</div>
      <div class="log-title-block">
        <strong>${log.title || "任务记录"}</strong>
        <small>${log.productId || "TASK"} · ${log.platform || "经营单元"} · ${log.store || "任务池"}</small>
        <span>${log.source || "系统"} · ${log.status || "已记录"}</span>
      </div>
    </div>
    <div class="log-action-block">
      <span>动作</span>
      <strong>${log.action || "任务池动作"}</strong>
      <small>${log.reason || "统一任务池记录。"}</small>
    </div>
    <div class="log-result-block">
      <span>结果</span>
      <strong>${log.result || "已写入日志。"}</strong>
    </div>
    <div class="log-actions">
      <button type="button" data-log-detail="${log.id}">详情</button>
      <button type="button" data-log-source="${log.route || "dashboard"}">查看来源</button>
      <button type="button" data-log-source="${log.taskRoute || "business-actions"}">关联任务</button>
    </div>
  </article>`;
}

function renderLogManager() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || !isLogRoute()) return;
  const logs = filteredLogs();
  activeLogId = null;
  title.textContent = "日志";
  appView.innerHTML = `<section class="log-toolbar">
    <div>
      <p class="eyebrow">OPERATION LOG · V1.1</p>
      <h2>任务池日志</h2>
      <p>记录任务创建、排序、置顶、完成、模块触发和用户操作；这里用于追溯，不做经营决策。</p>
    </div>
    <div class="log-filter-row">
      ${renderLogFilter("type", "类型")}
      ${renderLogFilter("source", "来源")}
      ${renderLogFilter("status", "状态")}
      <label class="log-search"><input type="search" value="${logFilters.search}" placeholder="搜索日志 / 商品" data-log-search /></label>
      <button type="button" class="log-export" data-log-export>导出日志</button>
    </div>
  </section>
  ${logNoticeMarkup()}
  <section class="kpi-grid log-metrics">
    ${logMetrics().map((item) => `<article class="card log-metric-card"><h3>${item.label}</h3><strong>${item.value}</strong><span class="card-desc">${item.desc}</span></article>`).join("")}
  </section>
  <section class="page-section log-list-section">
    <div class="section-header">
      <h3>日志流水</h3>
      <span class="status-badge">${logFilterSummary(logs.length)}</span>
    </div>
    <div class="log-card-list">
      ${logs.length ? logs.map(renderLogRow).join("") : `<div class="log-empty">当前筛选条件下没有日志。</div>`}
    </div>
  </section>`;
  bindLogButtons();
}

function renderLogDetail(logId) {
  const log = allLogs().find((item) => item.id === logId);
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!log || !appView || !title) return;
  activeLogId = logId;
  openLogFilter = null;
  title.textContent = "日志详情";
  appView.innerHTML = `<section class="log-detail-hero">
    <div class="log-detail-main">
      <div class="log-thumb large">${log.imageLabel || "记"}</div>
      <div>
        <p class="eyebrow">LOG DETAIL</p>
        <h2>${log.title || "任务记录"}</h2>
        <p>${log.time || "--:--"} · ${log.type || "任务记录"} · ${log.source || "系统"}</p>
        <span>${log.platform || "经营单元"} · ${log.store || "任务池"} · ${log.productId || "TASK"}</span>
      </div>
    </div>
    <div class="log-detail-actions">
      <button type="button" data-log-back>返回日志</button>
      <button type="button" data-log-source="${log.route || "dashboard"}">查看来源</button>
      <button type="button" data-log-source="${log.taskRoute || "business-actions"}">关联任务</button>
    </div>
  </section>
  ${logNoticeMarkup()}
  <section class="kpi-grid log-detail-metrics">
    <article class="card"><h3>类型</h3><strong>${log.type || "任务记录"}</strong><span class="card-desc">${log.status || "已记录"}</span></article>
    <article class="card"><h3>来源</h3><strong>${log.source || "系统"}</strong><span class="card-desc">${log.productId || "TASK"}</span></article>
    <article class="card"><h3>时间</h3><strong>${log.time || "--:--"}</strong><span class="card-desc">今日记录</span></article>
    <article class="card"><h3>状态</h3><strong class="metric-${logLevelClass(log.level)}">${log.status || "已记录"}</strong><span class="card-desc">可追溯</span></article>
  </section>
  <section class="page-section log-detail-section">
    <div class="section-header"><h3>动作</h3><span class="status-badge">${log.type || "任务记录"}</span></div>
    <p>${log.action || "任务池动作"}</p>
  </section>
  <section class="page-section log-detail-section">
    <div class="section-header"><h3>原因</h3><span class="status-badge pending">${log.source || "系统"}</span></div>
    <p>${log.reason || "统一任务池记录。"}</p>
  </section>
  <section class="page-section log-detail-section">
    <div class="section-header"><h3>结果</h3><span class="status-badge">${log.status || "已记录"}</span></div>
    <p>${log.result || "已写入日志。"}</p>
  </section>`;
  bindLogButtons();
}

function exportLogs() {
  const rows = filteredLogs();
  const header = ["时间", "类型", "来源", "状态", "商品/对象", "平台", "店铺", "动作", "原因", "结果"];
  const csvRows = [header, ...rows.map((item) => [item.time, item.type, item.source, item.status, item.title, item.platform, item.store, item.action, item.reason, item.result])]
    .map((row) => row.map((cell) => `"${String(cell || "").replaceAll('"', '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([`\ufeff${csvRows}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "operation-task-store-log.csv";
  link.click();
  URL.revokeObjectURL(url);
  logNotice = "当前筛选日志已导出。";
  renderLogManager();
}

function bindLogButtons() {
  document.querySelectorAll("[data-log-filter-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      openLogFilter = openLogFilter === button.dataset.logFilterToggle ? null : button.dataset.logFilterToggle;
      renderLogManager();
    });
  });
  document.querySelectorAll("[data-log-filter-value]").forEach((button) => {
    button.addEventListener("click", () => {
      const [type, value] = button.dataset.logFilterValue.split(":");
      logFilters[type] = value;
      openLogFilter = null;
      logNotice = "";
      renderLogManager();
    });
  });
  document.querySelector("[data-log-search]")?.addEventListener("input", (event) => {
    logFilters.search = event.target.value;
    renderLogManager();
    document.querySelector("[data-log-search]")?.focus();
  });
  document.querySelectorAll("[data-log-detail]").forEach((button) => {
    button.addEventListener("click", () => {
      logNotice = "";
      renderLogDetail(button.dataset.logDetail);
    });
  });
  document.querySelectorAll("[data-log-back]").forEach((button) => {
    button.addEventListener("click", () => {
      activeLogId = null;
      logNotice = "";
      renderLogManager();
    });
  });
  document.querySelectorAll("[data-log-source]").forEach((button) => {
    button.addEventListener("click", () => {
      location.hash = button.dataset.logSource;
    });
  });
  document.querySelector("[data-log-export]")?.addEventListener("click", exportLogs);
}

function scheduleLogPatch() {
  if (logRenderScheduled) return;
  logRenderScheduled = true;
  setTimeout(() => {
    logRenderScheduled = false;
    if (!isLogRoute()) return;
    if (activeLogId) renderLogDetail(activeLogId);
    else renderLogManager();
  }, 0);
}

const logObserver = new MutationObserver(() => {
  if (!isLogRoute()) return;
  if (document.querySelector(".log-toolbar") || document.querySelector(".log-detail-hero")) return;
  scheduleLogPatch();
});

logObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("operation-task-store-change", () => {
  if (isLogRoute()) scheduleLogPatch();
});
window.addEventListener("hashchange", () => {
  activeLogId = null;
  logNotice = "";
  openLogFilter = null;
  scheduleLogPatch();
});
window.addEventListener("load", scheduleLogPatch);
scheduleLogPatch();
