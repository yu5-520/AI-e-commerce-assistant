const logManagerPayload = {
  logs: [
    {
      id: "G001",
      time: "16:08",
      type: "任务完成",
      source: "流量触发",
      status: "已加入任务清单",
      level: "danger",
      imageLabel: "架",
      title: "厨房置物架免打孔收纳架壁挂多层家用置物架",
      platform: "拼多多",
      store: "家居百货店",
      productId: "P002",
      action: "搜索推广测试进入待办队列",
      reason: "ROI 1.1，退款率 6.8%，安装和尺寸咨询偏高。",
      result: "进入售后归因，暂不继续放大推广预算。",
      route: "business-traffic",
      taskRoute: "business-actions",
    },
    {
      id: "G002",
      time: "15:47",
      type: "用户操作",
      source: "上新触发",
      status: "已确认测试",
      level: "warning",
      imageLabel: "伞",
      title: "遮阳伞户外便携防晒防紫外线晴雨两用",
      platform: "淘宝",
      store: "家居生活主店",
      productId: "P001",
      action: "确认平台券活动价测试",
      reason: "活动测试进入确认期，需要同时观察 ROI、退款率和库存承接。",
      result: "进入待办执行队列，今天 20:00 前完成首轮观察。",
      route: "business-listing",
      taskRoute: "business-actions",
    },
    {
      id: "G003",
      time: "15:35",
      type: "AI 判定",
      source: "商品触发",
      status: "异常提醒",
      level: "danger",
      imageLabel: "垫",
      title: "护腰坐垫久坐办公室靠垫人体工学支撑款",
      platform: "抖音小店",
      store: "家居好物号",
      productId: "P003",
      action: "识别售后敏感商品",
      reason: "推荐流量 ROI 0.9，退款率 8.4%，材质和支撑感反馈集中。",
      result: "生成暂停投放和商品复查任务。",
      route: "business-products",
      taskRoute: "business-actions",
    },
    {
      id: "G004",
      time: "15:22",
      type: "数据动作",
      source: "报表触发",
      status: "已导入",
      level: "good",
      imageLabel: "表",
      title: "退款报表与商品报表同步检查",
      platform: "ERP / CRM",
      store: "家居生活店铺组",
      productId: "R001",
      action: "导入最新退款报表",
      reason: "流量测试和售后归因需要最新退款原因数据。",
      result: "更新退款原因字段，支持待办页售后归因任务。",
      route: "data-check",
      taskRoute: "business-actions",
    },
    {
      id: "G005",
      time: "15:10",
      type: "任务完成",
      source: "竞品触发",
      status: "已加入观察",
      level: "warning",
      imageLabel: "装",
      title: "厨房置物架：新增安装说明图 + 尺寸参照图版本",
      platform: "拼多多",
      store: "家居百货店",
      productId: "P002",
      action: "竞品机会转为上新测试",
      reason: "竞品差评集中在安装困难 / 尺寸不符。",
      result: "生成详情页测试版本，等待人工确认。",
      route: "business-competitors",
      taskRoute: "business-listing",
    },
    {
      id: "G006",
      time: "14:58",
      type: "用户操作",
      source: "商品触发",
      status: "已复制链接",
      level: "good",
      imageLabel: "盒",
      title: "透明收纳盒衣柜整理箱家用大容量防尘款",
      platform: "淘宝",
      store: "家居生活主店",
      productId: "P004",
      action: "复制商品链接",
      reason: "用户从商品经营列表查看库存告急商品。",
      result: "保留操作记录，便于回溯商品处理链路。",
      route: "business-products",
      taskRoute: "business-actions",
    },
    {
      id: "G007",
      time: "14:40",
      type: "AI 判定",
      source: "流量触发",
      status: "已生成任务",
      level: "warning",
      imageLabel: "盒",
      title: "透明收纳盒衣柜整理箱家用大容量防尘款",
      platform: "淘宝",
      store: "家居生活主店",
      productId: "P004",
      action: "判断库存承接不足",
      reason: "活动流量 ROI 1.3，但库存仅 46，接近安全线。",
      result: "生成补货周期确认任务，明天 12:00 前处理。",
      route: "business-traffic",
      taskRoute: "business-actions",
    },
    {
      id: "G008",
      time: "14:18",
      type: "数据动作",
      source: "报表触发",
      status: "已导出",
      level: "good",
      imageLabel: "表",
      title: "商品报表导出",
      platform: "ERP / CRM",
      store: "家居生活店铺组",
      productId: "R002",
      action: "导出商品报表 CSV",
      reason: "用户在报表页导出当前商品明细。",
      result: "本地生成 CSV 文件，未修改真实店铺数据。",
      route: "data-check",
      taskRoute: "business-actions",
    },
    {
      id: "G009",
      time: "13:55",
      type: "任务完成",
      source: "上新触发",
      status: "已加入任务清单",
      level: "warning",
      imageLabel: "推",
      title: "搜索推广测试：厨房置物架安装场景词",
      platform: "拼多多",
      store: "家居百货店",
      productId: "P002",
      action: "推广测试加入流量观察",
      reason: "上新测试需要观察点击成本、收藏加购和退款率。",
      result: "进入流量测试台，等待首轮数据回流。",
      route: "business-listing",
      taskRoute: "business-traffic",
    },
    {
      id: "G010",
      time: "09:00",
      type: "AI 判定",
      source: "经营单元",
      status: "已生成摘要",
      level: "good",
      imageLabel: "报",
      title: "生成经营日报和下一轮任务摘要",
      platform: "经营单元",
      store: "家居生活店铺组",
      productId: "DAILY",
      action: "汇总昨日任务和今日优先级",
      reason: "用于总览页任务摘要和日常复盘。",
      result: "输出到待办任务和总览任务清单。",
      route: "dashboard",
      taskRoute: "business-actions",
    },
  ],
};

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

function isLogRoute() {
  return location.hash.replace("#", "") === "business-report" || document.querySelector('.nav a[data-route="business-report"]')?.classList.contains("active");
}

function logLevelClass(level) {
  return level === "danger" ? "danger" : level === "warning" ? "warning" : "good";
}

function logNoticeMarkup() {
  if (!logNotice) return "";
  return `<section class="log-notice"><strong>操作结果</strong><span>${logNotice}</span></section>`;
}

function logFilterOptions(type) {
  if (type === "type") return ["全部类型", ...new Set(logManagerPayload.logs.map((item) => item.type))];
  if (type === "source") return ["全部来源", ...new Set(logManagerPayload.logs.map((item) => item.source))];
  return ["全部状态", ...new Set(logManagerPayload.logs.map((item) => item.status))];
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
  return logManagerPayload.logs.filter(logMatchesFilters);
}

function logMetrics() {
  const logs = logManagerPayload.logs;
  return [
    { label: "今日记录", value: logs.length, desc: "操作和系统记录" },
    { label: "任务完成", value: logs.filter((item) => item.type === "任务完成").length, desc: "进入任务闭环" },
    { label: "AI 判定", value: logs.filter((item) => item.type === "AI 判定").length, desc: "系统主动生成" },
    { label: "数据动作", value: logs.filter((item) => item.type === "数据动作").length, desc: "导入 / 导出 / 同步" },
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
      <strong>${log.time}</strong>
      <span>${log.type}</span>
    </div>
    <div class="log-title-cell">
      <div class="log-thumb">${log.imageLabel}</div>
      <div class="log-title-block">
        <strong>${log.title}</strong>
        <small>${log.productId} · ${log.platform} · ${log.store}</small>
        <span>${log.source} · ${log.status}</span>
      </div>
    </div>
    <div class="log-action-block">
      <span>动作</span>
      <strong>${log.action}</strong>
      <small>${log.reason}</small>
    </div>
    <div class="log-result-block">
      <span>结果</span>
      <strong>${log.result}</strong>
    </div>
    <div class="log-actions">
      <button type="button" data-log-detail="${log.id}">详情</button>
      <button type="button" data-log-source="${log.route}">查看来源</button>
      <button type="button" data-log-source="${log.taskRoute}">关联任务</button>
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
      <p class="eyebrow">OPERATION LOG</p>
      <h2>操作日志</h2>
      <p>记录任务完成、AI 自动判定、数据导入导出和用户操作；这里用于追溯，不做经营决策。</p>
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
  const log = logManagerPayload.logs.find((item) => item.id === logId);
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!log || !appView || !title) return;
  activeLogId = logId;
  openLogFilter = null;
  title.textContent = "日志详情";
  appView.innerHTML = `<section class="log-detail-hero">
    <div class="log-detail-main">
      <div class="log-thumb large">${log.imageLabel}</div>
      <div>
        <p class="eyebrow">LOG DETAIL</p>
        <h2>${log.title}</h2>
        <p>${log.time} · ${log.type} · ${log.source}</p>
        <span>${log.platform} · ${log.store} · ${log.productId}</span>
      </div>
    </div>
    <div class="log-detail-actions">
      <button type="button" data-log-back>返回日志</button>
      <button type="button" data-log-source="${log.route}">查看来源</button>
      <button type="button" data-log-source="${log.taskRoute}">关联任务</button>
    </div>
  </section>
  ${logNoticeMarkup()}
  <section class="kpi-grid log-detail-metrics">
    <article class="card"><h3>类型</h3><strong>${log.type}</strong><span class="card-desc">${log.status}</span></article>
    <article class="card"><h3>来源</h3><strong>${log.source}</strong><span class="card-desc">${log.productId}</span></article>
    <article class="card"><h3>时间</h3><strong>${log.time}</strong><span class="card-desc">今日记录</span></article>
    <article class="card"><h3>状态</h3><strong class="metric-${logLevelClass(log.level)}">${log.status}</strong><span class="card-desc">可追溯</span></article>
  </section>
  <section class="page-section log-detail-section">
    <div class="section-header"><h3>动作</h3><span class="status-badge">${log.type}</span></div>
    <p>${log.action}</p>
  </section>
  <section class="page-section log-detail-section">
    <div class="section-header"><h3>原因</h3><span class="status-badge pending">${log.source}</span></div>
    <p>${log.reason}</p>
  </section>
  <section class="page-section log-detail-section">
    <div class="section-header"><h3>结果</h3><span class="status-badge">${log.status}</span></div>
    <p>${log.result}</p>
  </section>`;
  bindLogButtons();
}

function exportLogs() {
  const rows = filteredLogs();
  const header = ["时间", "类型", "来源", "状态", "商品/对象", "平台", "店铺", "动作", "原因", "结果"];
  const csvRows = [header, ...rows.map((item) => [item.time, item.type, item.source, item.status, item.title, item.platform, item.store, item.action, item.reason, item.result])]
    .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([`\ufeff${csvRows}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "operation-log.csv";
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
window.addEventListener("hashchange", () => {
  activeLogId = null;
  logNotice = "";
  openLogFilter = null;
  scheduleLogPatch();
});
window.addEventListener("load", scheduleLogPatch);
scheduleLogPatch();
