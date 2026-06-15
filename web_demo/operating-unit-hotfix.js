const operatingUnitPayload = {
  name: "家居生活店铺组",
  subtitle: "淘宝 / 拼多多 / 抖音小店 · 4 家店铺 · 每天同步",
  dataMode: "Mock 数据",
  nextSystem: "聚水潭待接入",
  metrics: [
    { label: "平台数量", value: "3", desc: "淘宝 / 拼多多 / 抖音" },
    { label: "店铺数量", value: "4", desc: "统一归入店铺组" },
    { label: "已接入数据", value: "4 类", desc: "商品 / 库存 / 订单 / 售后" },
    { label: "待接入系统", value: "2", desc: "聚水潭 / 广告后台" },
  ],
  shops: [
    { platform: "淘宝", name: "家居生活主店", status: "已连接", data: "商品 / 订单 / 库存" },
    { platform: "拼多多", name: "家居百货店", status: "已连接", data: "商品 / 售后" },
    { platform: "拼多多", name: "家清收纳店", status: "已连接", data: "商品 / 订单" },
    { platform: "抖音小店", name: "家居好物号", status: "待授权", data: "暂未同步" },
  ],
  dataSources: [
    { system: "ERP", status: "已接入 Mock", usage: "商品、库存、成本" },
    { system: "CRM", status: "已接入 Mock", usage: "客户、售后、退款" },
    { system: "聚水潭", status: "待接入", usage: "多平台店铺数据汇总" },
    { system: "广告后台", status: "待接入", usage: "ROI、投放、转化" },
  ],
};

function renderOperatingUnitStoreGroup() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || title.textContent.trim() !== "经营单元") return;

  appView.innerHTML = `<section class="unit-hero">
    <div>
      <p class="eyebrow">STORE GROUP</p>
      <h2>${operatingUnitPayload.name}</h2>
      <p>${operatingUnitPayload.subtitle}</p>
    </div>
    <div class="unit-hero-side">
      <span>数据源</span>
      <strong>${operatingUnitPayload.dataMode}</strong>
      <small>${operatingUnitPayload.nextSystem}</small>
    </div>
  </section>

  <section class="kpi-grid unit-metrics">
    ${operatingUnitPayload.metrics.map((item) => `<article class="card unit-metric-card"><h3>${item.label}</h3><strong>${item.value}</strong><span class="card-desc">${item.desc}</span></article>`).join("")}
  </section>

  <section class="page-section unit-store-section">
    <div class="section-header">
      <h3>关联店铺</h3>
      <span class="status-badge">店铺群</span>
    </div>
    <div class="unit-store-table">
      ${operatingUnitPayload.shops.map((shop) => `<article class="unit-store-row">
        <strong>${shop.platform}</strong>
        <span>${shop.name}</span>
        <em>${shop.status}</em>
        <small>${shop.data}</small>
      </article>`).join("")}
    </div>
  </section>

  <section class="page-section unit-store-section">
    <div class="section-header">
      <h3>数据接入状态</h3>
      <span class="status-badge pending">可扩展</span>
    </div>
    <div class="unit-store-table">
      ${operatingUnitPayload.dataSources.map((source) => `<article class="unit-store-row">
        <strong>${source.system}</strong>
        <span>${source.status}</span>
        <em>${source.usage}</em>
        <small>经营单元数据来源</small>
      </article>`).join("")}
    </div>
  </section>`;
}

function scheduleOperatingUnitPatch() {
  setTimeout(renderOperatingUnitStoreGroup, 0);
  setTimeout(renderOperatingUnitStoreGroup, 120);
  setTimeout(renderOperatingUnitStoreGroup, 500);
}

const operatingUnitObserver = new MutationObserver(() => {
  const title = document.getElementById("pageTitle")?.textContent?.trim();
  if (title === "经营单元") scheduleOperatingUnitPatch();
});

operatingUnitObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("hashchange", scheduleOperatingUnitPatch);
window.addEventListener("load", scheduleOperatingUnitPatch);
scheduleOperatingUnitPatch();
