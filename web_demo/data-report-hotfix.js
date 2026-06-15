const reportManagerPayload = {
  title: "ERP / CRM 报表管理",
  subtitle: "统一查看商品、订单、库存、退款和客户报表，支撑任务清单和经营判断。",
  metrics: [
    { label: "已接入系统", value: "2", desc: "ERP / CRM Mock" },
    { label: "报表数量", value: "7", desc: "商品、订单、库存、售后、客户" },
    { label: "最近同步", value: "12:30", desc: "每天自动同步" },
    { label: "待接入", value: "聚水潭", desc: "多店铺汇总" },
  ],
  groups: [
    {
      title: "ERP 报表",
      reports: [
        { id: "products", name: "商品报表", source: "ERP", status: "已同步", count: "128 条", desc: "商品、库存、成本、售价、毛利率" },
        { id: "orders", name: "订单报表", source: "ERP", status: "已同步", count: "932 条", desc: "订单金额、发货状态、下单时间" },
        { id: "inventory", name: "库存报表", source: "ERP", status: "已同步", count: "128 条", desc: "库存数量、预警、补货状态" },
      ],
    },
    {
      title: "CRM 报表",
      reports: [
        { id: "refunds", name: "退款报表", source: "CRM", status: "已同步", count: "37 条", desc: "退款原因、售后状态、责任归因" },
        { id: "customers", name: "客户报表", source: "CRM", status: "已同步", count: "584 人", desc: "客户来源、复购、风险标记" },
        { id: "tags", name: "客户标签报表", source: "CRM", status: "已同步", count: "9 类", desc: "复购、价格敏感、售后敏感" },
        { id: "interactions", name: "客户互动报表", source: "CRM", status: "已同步", count: "216 条", desc: "咨询、评价、售后沟通" },
      ],
    },
  ],
  details: {
    products: {
      title: "商品报表",
      source: "ERP",
      summary: [
        { label: "商品数", value: "128" },
        { label: "高风险商品", value: "3" },
        { label: "库存异常", value: "8" },
        { label: "售后敏感", value: "4" },
        { label: "最近同步", value: "12:30" },
      ],
      columns: ["商品ID", "商品名称", "平台", "店铺", "库存", "成本", "售价", "毛利率", "状态"],
      rows: [
        ["P001", "遮阳伞", "淘宝", "家居生活主店", "200", "18", "39", "53%", "正常"],
        ["P002", "厨房置物架", "拼多多", "家居百货店", "120", "22", "49", "55%", "库存偏高"],
        ["P003", "护腰坐垫", "抖音小店", "家居好物号", "80", "35", "69", "49%", "售后敏感"],
      ],
    },
    orders: {
      title: "订单报表",
      source: "ERP",
      summary: [
        { label: "今日订单", value: "86" },
        { label: "已发货", value: "61" },
        { label: "待发货", value: "18" },
        { label: "退款中", value: "7" },
      ],
      columns: ["订单号", "平台", "店铺", "商品", "金额", "状态", "下单时间"],
      rows: [
        ["O001", "淘宝", "家居生活主店", "遮阳伞", "39", "已发货", "10:24"],
        ["O002", "拼多多", "家居百货店", "厨房置物架", "49", "待发货", "11:06"],
        ["O003", "抖音小店", "家居好物号", "护腰坐垫", "69", "退款中", "11:42"],
      ],
    },
    inventory: {
      title: "库存报表",
      source: "ERP",
      summary: [
        { label: "SKU 数", value: "128" },
        { label: "库存偏高", value: "8" },
        { label: "库存偏低", value: "5" },
        { label: "待补货", value: "3" },
      ],
      columns: ["SKU", "商品", "平台", "店铺", "库存", "安全库存", "状态"],
      rows: [
        ["SKU001", "遮阳伞", "淘宝", "家居生活主店", "200", "80", "库存偏高"],
        ["SKU002", "厨房置物架", "拼多多", "家居百货店", "120", "60", "正常"],
        ["SKU003", "护腰坐垫", "抖音小店", "家居好物号", "80", "100", "待补货"],
      ],
    },
    refunds: {
      title: "退款报表",
      source: "CRM",
      summary: [
        { label: "退款记录", value: "37" },
        { label: "尺码问题", value: "9" },
        { label: "材质问题", value: "6" },
        { label: "物流问题", value: "4" },
      ],
      columns: ["退款ID", "平台", "商品", "金额", "原因", "状态", "处理建议"],
      rows: [
        ["R001", "抖音小店", "护腰坐垫", "69", "材质偏软", "处理中", "补充材质说明"],
        ["R002", "淘宝", "遮阳伞", "39", "物流延迟", "已完成", "复查物流承诺"],
        ["R003", "拼多多", "厨房置物架", "49", "尺寸不符", "处理中", "补尺寸参照图"],
      ],
    },
    customers: {
      title: "客户报表",
      source: "CRM",
      summary: [
        { label: "客户数", value: "584" },
        { label: "复购客户", value: "96" },
        { label: "售后敏感", value: "23" },
        { label: "高价值", value: "41" },
      ],
      columns: ["客户ID", "来源平台", "最近购买", "消费金额", "标签", "状态"],
      rows: [
        ["C001", "淘宝", "遮阳伞", "156", "复购", "正常"],
        ["C002", "拼多多", "厨房置物架", "49", "价格敏感", "观察"],
        ["C003", "抖音小店", "护腰坐垫", "69", "售后敏感", "需跟进"],
      ],
    },
    tags: {
      title: "客户标签报表",
      source: "CRM",
      summary: [
        { label: "标签数", value: "9" },
        { label: "复购", value: "96" },
        { label: "价格敏感", value: "141" },
        { label: "售后敏感", value: "23" },
      ],
      columns: ["标签", "人数", "来源", "用途", "建议动作"],
      rows: [
        ["复购", "96", "订单", "活动触达", "优先推荐套装"],
        ["价格敏感", "141", "咨询/订单", "优惠判断", "控制折扣边界"],
        ["售后敏感", "23", "退款/互动", "客服承接", "人工复核话术"],
      ],
    },
    interactions: {
      title: "客户互动报表",
      source: "CRM",
      summary: [
        { label: "互动数", value: "216" },
        { label: "咨询", value: "132" },
        { label: "评价", value: "51" },
        { label: "售后", value: "33" },
      ],
      columns: ["互动ID", "平台", "客户", "类型", "内容摘要", "处理状态"],
      rows: [
        ["I001", "淘宝", "C001", "咨询", "询问遮阳伞尺寸", "已回复"],
        ["I002", "拼多多", "C002", "评价", "置物架安装反馈", "已记录"],
        ["I003", "抖音小店", "C003", "售后", "护腰坐垫支撑不足", "待跟进"],
      ],
    },
  },
};

let activeReportId = null;

function isReportRoute() {
  return location.hash.replace("#", "") === "data-check" || document.querySelector('.nav a[data-route="data-check"]')?.classList.contains("active");
}

function setReportNavLabel() {
  const nav = document.querySelector('.nav a[data-route="data-check"]');
  if (nav) nav.textContent = "报表";
}

function renderReportManager() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || !isReportRoute()) return;
  title.textContent = reportManagerPayload.title;
  activeReportId = null;
  appView.innerHTML = `<section class="report-hero">
    <div>
      <p class="eyebrow">REPORT CENTER</p>
      <h2>${reportManagerPayload.title}</h2>
      <p>${reportManagerPayload.subtitle}</p>
    </div>
    <div class="report-hero-side">
      <span>数据来源</span>
      <strong>ERP / CRM</strong>
      <small>聚水潭待接入</small>
    </div>
  </section>
  <section class="kpi-grid report-metrics">
    ${reportManagerPayload.metrics.map((item) => `<article class="card report-metric-card"><h3>${item.label}</h3><strong>${item.value}</strong><span class="card-desc">${item.desc}</span></article>`).join("")}
  </section>
  ${reportManagerPayload.groups.map((group) => `<section class="page-section report-section">
    <div class="section-header"><h3>${group.title}</h3><span class="status-badge">可查看</span></div>
    <div class="report-card-list">
      ${group.reports.map((report) => `<article class="report-card">
        <div>
          <h3>${report.name}</h3>
          <p>${report.desc}</p>
          <div class="report-meta"><span>${report.source}</span><span>${report.status}</span><span>${report.count}</span></div>
        </div>
        <button type="button" data-report-id="${report.id}">查看报表</button>
      </article>`).join("")}
    </div>
  </section>`).join("")}`;
  bindReportButtons();
}

function renderReportDetail(reportId) {
  const report = reportManagerPayload.details[reportId];
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!report || !appView || !title) return;
  activeReportId = reportId;
  title.textContent = report.title;
  appView.innerHTML = `<section class="report-detail-hero">
    <div>
      <p class="eyebrow">${report.source} REPORT</p>
      <h2>${report.title}</h2>
      <p>从报表明细进入真实经营判断，避免只看系统状态。</p>
    </div>
    <div class="report-actions">
      <button type="button" data-report-back>返回报表管理</button>
      <button type="button">重新同步</button>
      <button type="button">导出报表</button>
    </div>
  </section>
  <section class="kpi-grid report-metrics">
    ${report.summary.map((item) => `<article class="card report-metric-card"><h3>${item.label}</h3><strong>${item.value}</strong></article>`).join("")}
  </section>
  <section class="page-section report-table-section">
    <div class="section-header"><h3>报表明细</h3><span class="status-badge">Mock 数据</span></div>
    <div class="report-table-wrap">
      <table class="report-table">
        <thead><tr>${report.columns.map((col) => `<th>${col}</th>`).join("")}</tr></thead>
        <tbody>${report.rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody>
      </table>
    </div>
  </section>`;
  document.querySelector("[data-report-back]")?.addEventListener("click", renderReportManager);
}

function bindReportButtons() {
  document.querySelectorAll("[data-report-id]").forEach((button) => {
    button.addEventListener("click", () => renderReportDetail(button.dataset.reportId));
  });
}

function scheduleReportPatch() {
  setReportNavLabel();
  setTimeout(() => {
    if (!isReportRoute()) return;
    if (activeReportId) renderReportDetail(activeReportId);
    else renderReportManager();
  }, 0);
  setTimeout(() => {
    if (!isReportRoute()) return;
    if (!document.querySelector(".report-hero") && !document.querySelector(".report-detail-hero")) renderReportManager();
  }, 160);
}

const reportObserver = new MutationObserver(() => {
  setReportNavLabel();
  if (isReportRoute()) scheduleReportPatch();
});

reportObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("hashchange", () => { activeReportId = null; scheduleReportPatch(); });
window.addEventListener("load", scheduleReportPatch);
scheduleReportPatch();
