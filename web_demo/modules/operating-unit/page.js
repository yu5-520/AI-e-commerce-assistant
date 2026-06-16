(function () {
  window.OperatingUnitPage = {
    route: "operating-unit",
    title: "经营单元",
    render() {
      const shops = [["淘宝", "家居生活主店", "已连接", "商品 / 订单 / 库存"], ["拼多多", "家居百货店", "已连接", "商品 / 售后"], ["拼多多", "家清收纳店", "已连接", "商品 / 订单"], ["抖音小店", "家居好物号", "待授权", "暂未同步"]];
      const sources = [["ERP", "已接入 Mock", "商品、库存、成本"], ["CRM", "已接入 Mock", "客户、售后、退款"], ["聚水潭", "待接入", "多平台店铺数据汇总"], ["广告后台", "待接入", "ROI、投放、转化"]];
      return `<section class="unit-hero"><div><p class="eyebrow">STORE GROUP</p><h2>家居生活店铺组</h2><p>淘宝 / 拼多多 / 抖音小店 · 4 家店铺 · 每天同步</p></div><div class="unit-hero-side"><span>数据源</span><strong>Mock 数据</strong><small>聚水潭待接入</small></div></section>
      <section class="kpi-grid unit-metrics">${[["平台数量", "3", "淘宝 / 拼多多 / 抖音"], ["店铺数量", "4", "统一归入店铺组"], ["已接入数据", "4 类", "商品 / 库存 / 订单 / 售后"], ["待接入系统", "2", "聚水潭 / 广告后台"]].map(([a,b,c]) => `<article class="card unit-metric-card"><h3>${a}</h3><strong>${b}</strong><span class="card-desc">${c}</span></article>`).join("")}</section>
      <section class="page-section unit-store-section"><div class="section-header"><h3>关联店铺</h3><span class="status-badge">店铺群</span></div><div class="unit-store-table">${shops.map(([platform, name, status, data]) => `<article class="unit-store-row"><strong>${platform}</strong><span>${name}</span><em>${status}</em><small>${data}</small></article>`).join("")}</div></section>
      <section class="page-section unit-store-section"><div class="section-header"><h3>数据接入状态</h3><span class="status-badge pending">可扩展</span></div><div class="unit-store-table">${sources.map(([system, status, usage]) => `<article class="unit-store-row"><strong>${system}</strong><span>${status}</span><em>${usage}</em><small>经营单元数据来源</small></article>`).join("")}</div></section>`;
    },
  };
})();
