const dashboardLinkedTaskPool = [
  {
    id: "A001",
    rank: 1,
    priority: "高",
    urgency: "紧急",
    urgencyLevel: "high",
    deadline: "今天 18:00 前",
    source: "流量触发 / AI 自动判定",
    sourceModule: "流量测试台",
    sourceRoute: "business-traffic",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P002",
    imageLabel: "架",
    title: "先查售后，不继续放大推广预算",
    productTitle: "厨房置物架免打孔收纳架壁挂多层家用置物架",
    platform: "拼多多",
    store: "家居百货店",
    reason: "搜索推广 ROI 1.1，退款率 6.8%，安装和尺寸咨询偏高。",
    impact: "退款率 / ROI",
    count: 1,
    status: "待确认",
  },
  {
    id: "A002",
    rank: 2,
    priority: "高",
    urgency: "紧急",
    urgencyLevel: "high",
    deadline: "今天内",
    source: "商品触发 / AI 自动判定",
    sourceModule: "商品经营列表",
    sourceRoute: "business-products",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P003",
    imageLabel: "垫",
    title: "暂停投放并复查售后敏感商品",
    productTitle: "护腰坐垫久坐办公室靠垫人体工学支撑款",
    platform: "抖音小店",
    store: "家居好物号",
    reason: "推荐流量 ROI 0.9，退款率 8.4%，材质和支撑感反馈集中。",
    impact: "售后 / 商品复查",
    count: 1,
    status: "待确认",
  },
  {
    id: "A003",
    rank: 3,
    priority: "高",
    urgency: "紧急",
    urgencyLevel: "high",
    deadline: "今天 20:00 前",
    source: "上新触发",
    sourceModule: "上新测试台",
    sourceRoute: "business-listing",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P001",
    imageLabel: "伞",
    title: "确认平台券活动价和利润安全线",
    productTitle: "遮阳伞户外便携防晒防紫外线晴雨两用",
    platform: "淘宝",
    store: "家居生活主店",
    reason: "活动测试进入确认期，需要同时观察 ROI、退款率和库存承接。",
    impact: "活动 / 库存承接",
    count: 1,
    status: "待确认",
  },
  {
    id: "A004",
    rank: 4,
    priority: "中",
    urgency: "中",
    urgencyLevel: "medium",
    deadline: "明天 12:00 前",
    source: "商品触发 / 流量触发",
    sourceModule: "商品经营列表",
    sourceRoute: "business-products",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P004",
    imageLabel: "盒",
    title: "确认补货周期，再决定是否继续活动流量",
    productTitle: "透明收纳盒衣柜整理箱家用大容量防尘款",
    platform: "淘宝",
    store: "家居生活主店",
    reason: "库存 46，接近安全线；活动流量 ROI 1.3，可谨慎放量。",
    impact: "库存承接",
    count: 1,
    status: "待确认",
  },
  {
    id: "A005",
    rank: 5,
    priority: "中",
    urgency: "中",
    urgencyLevel: "medium",
    deadline: "明天 18:00 前",
    source: "竞品触发",
    sourceModule: "竞品观察列表",
    sourceRoute: "business-competitors",
    todoRoute: "business-actions",
    productRoute: "business-products",
    logRoute: "business-report",
    productId: "P002",
    imageLabel: "装",
    title: "确认竞品机会测试版本",
    productTitle: "厨房置物架：新增安装说明图 + 尺寸参照图版本",
    platform: "拼多多",
    store: "家居百货店",
    reason: "竞品差评集中在安装困难 / 尺寸不符，可转为详情页测试动作。",
    impact: "竞品机会 / 上新",
    count: 1,
    status: "待确认",
  },
  {
    id: "A007",
    rank: 6,
    priority: "低",
    urgency: "观察",
    urgencyLevel: "low",
    deadline: "本周内",
    source: "报表触发",
    sourceModule: "ERP / CRM 报表管理",
    sourceRoute: "data-check",
    todoRoute: "business-actions",
    productRoute: "data-check",
    logRoute: "business-report",
    productId: "R001",
    imageLabel: "表",
    title: "导入最新退款报表，支撑售后归因",
    productTitle: "退款报表与商品报表同步检查",
    platform: "ERP / CRM",
    store: "家居生活店铺组",
    reason: "流量测试和售后归因需要最新退款原因数据。",
    impact: "报表 / 售后归因",
    count: 1,
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
    { title: "可测试机会", value: tasks.filter((task) => ["上新触发", "竞品触发"].some((source) => task.source.includes(source))).length, desc: "来自上新 / 竞品" },
  ];
}

function dashboardNowLabel(date = new Date()) {
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]} · ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")} 更新`;
}

function linkedBadge(level, text) {
  return `<span class="badge ${level || "low"}">${text}</span>`;
}

function renderLinkedDashboardTask(task, index) {
  return `<article class="dashboard-task-card dashboard-linked-task">
    <div class="task-rank">${index + 1}</div>
    <div class="dashboard-linked-main">
      <div class="dashboard-linked-title-row">
        <div class="dashboard-linked-thumb">${task.imageLabel}</div>
        <div>
          <h3>${task.title}</h3>
          <strong>${task.productTitle}</strong>
          <small>${task.productId} · ${task.platform} · ${task.store}</small>
        </div>
      </div>
      <div class="task-meta dashboard-linked-meta">
        ${linkedBadge(task.urgencyLevel, task.urgency)}
        <span>${task.deadline}</span>
        <span>${task.source}</span>
        <span>${task.impact}</span>
      </div>
      <p>${task.reason}</p>
    </div>
    <div class="dashboard-linked-actions">
      <button type="button" data-dashboard-route="${task.todoRoute}">进入待办</button>
      <button type="button" data-dashboard-route="${task.sourceRoute}">查看来源</button>
      <button type="button" data-dashboard-route="${task.productRoute}">查看商品</button>
      <button type="button" data-dashboard-complete="${task.id}">标记完成</button>
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
      <p class="eyebrow">TASK BOARD</p>
      <h2>任务清单</h2>
      <p class="dashboard-time">${dashboardNowLabel()}</p>
    </div>
    <div class="dashboard-status-side">
      <span>经营单元</span>
      <strong>家居生活商品</strong>
      <small>跨模块任务 · ${tasks.length} 项待办</small>
    </div>
  </section>
  <section class="kpi-grid dashboard-metrics dashboard-linked-metrics">
    ${metrics.map((item) => `<article class="card metric-card"><h3>${item.title}</h3><strong>${item.value}</strong><span class="card-desc">${item.desc}</span></article>`).join("")}
  </section>
  <section class="page-section dashboard-queue dashboard-linked-queue">
    <div class="section-header dashboard-linked-header">
      <div>
        <h3>处理顺序</h3>
        <span class="status-badge">跨模块实时任务</span>
      </div>
      <button type="button" data-dashboard-route="business-actions">查看全部待办</button>
    </div>
    <section class="dashboard-task-list">
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
