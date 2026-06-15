const dashboardLinkedTaskPool = [
  {
    id: "A001",
    rank: 1,
    priority: "高",
    urgency: "紧急",
    urgencyLevel: "high",
    deadline: "今天 18:00 前",
    timeBucket: "今天 18:00 前",
    source: "流量 / AI 判定",
    sourceModule: "流量测试台",
    sourceRoute: "business-traffic",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P002",
    imageLabel: "架",
    taskType: "售后优先",
    taskSignal: "先查售后",
    productShort: "厨房置物架",
    productTitle: "厨房置物架免打孔收纳架壁挂多层家用置物架",
    platform: "拼多多",
    store: "家居百货店",
    judgmentTags: ["ROI 低", "退款率高", "尺寸咨询高"],
    impact: "退款率 / ROI",
    status: "待确认",
  },
  {
    id: "A002",
    rank: 2,
    priority: "高",
    urgency: "紧急",
    urgencyLevel: "high",
    deadline: "今天内",
    timeBucket: "今天内",
    source: "商品 / AI 判定",
    sourceModule: "商品经营列表",
    sourceRoute: "business-products",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P003",
    imageLabel: "垫",
    taskType: "商品复查",
    taskSignal: "暂停投放",
    productShort: "护腰坐垫",
    productTitle: "护腰坐垫久坐办公室靠垫人体工学支撑款",
    platform: "抖音小店",
    store: "家居好物号",
    judgmentTags: ["ROI 低", "退款异常", "售后敏感"],
    impact: "售后 / 商品复查",
    status: "待确认",
  },
  {
    id: "A003",
    rank: 3,
    priority: "高",
    urgency: "紧急",
    urgencyLevel: "high",
    deadline: "今天 20:00 前",
    timeBucket: "今天 20:00 前",
    source: "上新",
    sourceModule: "上新测试台",
    sourceRoute: "business-listing",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P001",
    imageLabel: "伞",
    taskType: "活动价确认",
    taskSignal: "确认利润线",
    productShort: "遮阳伞",
    productTitle: "遮阳伞户外便携防晒防紫外线晴雨两用",
    platform: "淘宝",
    store: "家居生活主店",
    judgmentTags: ["活动测试", "利润安全线", "库存承接"],
    impact: "活动 / 库存承接",
    status: "待确认",
  },
  {
    id: "A004",
    rank: 4,
    priority: "中",
    urgency: "中",
    urgencyLevel: "medium",
    deadline: "明天 12:00 前",
    timeBucket: "明天前",
    source: "商品 / 流量",
    sourceModule: "商品经营列表",
    sourceRoute: "business-products",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P004",
    imageLabel: "盒",
    taskType: "库存承接",
    taskSignal: "确认补货周期",
    productShort: "收纳盒",
    productTitle: "透明收纳盒衣柜整理箱家用大容量防尘款",
    platform: "淘宝",
    store: "家居生活主店",
    judgmentTags: ["库存低", "活动流量", "谨慎放量"],
    impact: "库存承接",
    status: "待确认",
  },
  {
    id: "A005",
    rank: 5,
    priority: "中",
    urgency: "中",
    urgencyLevel: "medium",
    deadline: "明天 18:00 前",
    timeBucket: "明天前",
    source: "竞品",
    sourceModule: "竞品观察列表",
    sourceRoute: "business-competitors",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P002",
    imageLabel: "装",
    taskType: "竞品机会",
    taskSignal: "确认测试版本",
    productShort: "厨房置物架",
    productTitle: "厨房置物架：新增安装说明图 + 尺寸参照图版本",
    platform: "拼多多",
    store: "家居百货店",
    judgmentTags: ["安装差评", "尺寸差评", "可转上新"],
    impact: "竞品机会 / 上新",
    status: "待确认",
  },
  {
    id: "A007",
    rank: 6,
    priority: "低",
    urgency: "观察",
    urgencyLevel: "low",
    deadline: "本周内",
    timeBucket: "本周内",
    source: "报表",
    sourceModule: "ERP / CRM 报表管理",
    sourceRoute: "data-check",
    todoRoute: "business-actions",
    productRoute: "data-check",
    logRoute: "business-report",
    productId: "R001",
    imageLabel: "表",
    taskType: "报表补齐",
    taskSignal: "导入退款报表",
    productShort: "退款报表",
    productTitle: "退款报表与商品报表同步检查",
    platform: "ERP / CRM",
    store: "家居生活店铺组",
    judgmentTags: ["数据缺口", "售后归因", "复盘需要"],
    impact: "报表 / 售后归因",
    status: "待确认",
  },
];

const dashboardDoneState = {};
let dashboardLinkedRenderScheduled = false;

function isLinkedDashboardRoute() {
  const route = location.hash.replace("#", "") || "dashboard";
  return route === "dashboard" || document.querySelector('.nav a[data-route="dashboard"]')?.classList.contains("active");
}

function activeDashboardTasks() {
  return dashboardLinkedTaskPool
    .filter((task) => dashboardDoneState[task.id] !== "已完成")
    .sort((a, b) => a.rank - b.rank);
}

function dashboardMetrics(tasks) {
  return [
    { title: "紧急任务", value: tasks.filter((task) => task.priority === "高").length, desc: "优先处理" },
    { title: "到期任务", value: tasks.filter((task) => task.deadline.includes("今天")).length, desc: "有时间限制" },
    { title: "待确认", value: tasks.filter((task) => task.status === "待确认").length, desc: "确认前不执行" },
    { title: "可测试机会", value: tasks.filter((task) => ["上新", "竞品"].some((source) => task.source.includes(source))).length, desc: "来自上新 / 竞品" },
  ];
}

function dashboardTimeBuckets(tasks) {
  const order = ["今天 18:00 前", "今天 20:00 前", "今天内", "明天前", "本周内"];
  return order
    .map((label) => ({ label, count: tasks.filter((task) => task.timeBucket === label).length }))
    .filter((item) => item.count > 0);
}

function dashboardNowLabel(date = new Date()) {
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]} · ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")} 更新`;
}

function linkedBadge(level, text) {
  return `<span class="badge ${level || "low"}">${text}</span>`;
}

function renderDashboardTimeSystem(tasks) {
  const buckets = dashboardTimeBuckets(tasks);
  return `<section class="dashboard-time-system">
    <div><strong>时间系统</strong><span>按截止时间自动分组</span></div>
    <div class="dashboard-time-chips">
      ${buckets.map((item) => `<span>${item.label}<strong>${item.count}</strong></span>`).join("")}
    </div>
  </section>`;
}

function renderDashboardJudgmentTags(task) {
  return `<div class="dashboard-judgment-tags">${task.judgmentTags.map((tag) => `<span>${tag}</span>`).join("")}</div>`;
}

function renderLinkedDashboardTask(task, index) {
  return `<article class="dashboard-task-card dashboard-linked-task dashboard-schedule-row">
    <div class="task-rank">${index + 1}</div>
    <div class="dashboard-schedule-time">
      <span>${task.priority}</span>
      <strong>${task.deadline}</strong>
    </div>
    <div class="dashboard-schedule-main">
      <div class="dashboard-linked-thumb">${task.imageLabel}</div>
      <div class="dashboard-schedule-copy">
        <div class="dashboard-schedule-title-line">
          <h3>${task.taskType}</h3>
          <span>${task.taskSignal}</span>
        </div>
        <strong>${task.productShort}</strong>
        <small>${task.productId} · ${task.platform} · ${task.store}</small>
      </div>
    </div>
    <div class="dashboard-schedule-source">
      <span>来源</span>
      <strong>${task.source}</strong>
      <small>${task.sourceModule}</small>
    </div>
    <div class="dashboard-schedule-judgment">
      <span>判断</span>
      ${renderDashboardJudgmentTags(task)}
    </div>
    <div class="dashboard-linked-actions">
      <button type="button" data-dashboard-route="${task.todoRoute}">进入待办</button>
      <button type="button" data-dashboard-route="${task.sourceRoute}">查看来源</button>
      <button type="button" class="secondary" data-dashboard-route="${task.productRoute}">商品</button>
      <button type="button" class="ghost" data-dashboard-complete="${task.id}">完成</button>
    </div>
  </article>`;
}

function renderLinkedDashboard() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || !isLinkedDashboardRoute()) return;
  const tasks = activeDashboardTasks();
  const topTasks = tasks.slice(0, 5);
  const metrics = dashboardMetrics(tasks);
  title.textContent = "总览";
  appView.innerHTML = `<section class="dashboard-status dashboard-linked-board">
    <div class="dashboard-status-main">
      <p class="eyebrow">COMMAND BOARD</p>
      <h2>任务清单</h2>
      <p class="dashboard-time">${dashboardNowLabel()}</p>
    </div>
    <div class="dashboard-status-side">
      <span>经营单元</span>
      <strong>家居生活商品</strong>
      <small>导航台 · ${tasks.length} 项待办</small>
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
        <span class="status-badge">导航 / 时间 / 判断</span>
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
      const taskId = button.dataset.dashboardComplete;
      dashboardDoneState[taskId] = "已完成";
      renderLinkedDashboard();
      setTimeout(() => {
        const notice = document.createElement("section");
        notice.className = "dashboard-done-notice";
        notice.textContent = "已从首页移除，处理记录进入日志。";
        document.querySelector(".dashboard-linked-board")?.after(notice);
      }, 0);
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
window.addEventListener("hashchange", () => setTimeout(renderLinkedDashboard, 0));
window.addEventListener("load", () => setTimeout(renderLinkedDashboard, 0));
setTimeout(renderLinkedDashboard, 0);
setTimeout(renderLinkedDashboard, 250);
setTimeout(renderLinkedDashboard, 1000);
