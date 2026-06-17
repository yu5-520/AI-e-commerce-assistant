(function () {
  const s = (value) => AppShell.escape(value);
  function storeRow(store) {
    return `<article class="unit-store-row"><strong>${s(store.platform)}</strong><span>${s(store.name)}</span><em>${s(store.primaryOperatorName || "未分配")}</em><small>${s(store.reviewerName || "店群总管")}复核</small></article>`;
  }
  window.OperatingUnitPage = {
    route: "operating-unit",
    title: "经营单元",
    async render() {
      const payload = await AppApi.operatingUnit();
      const stores = payload?.stores || [];
      const sources = [["ERP", "已接入 Mock", "商品、库存、成本"], ["CRM", "已接入 Mock", "客户、售后、退款"], ["报表上传", "已接入", "CSV 预检与预警"], ["聚水潭", "待接入", "多平台店铺数据汇总"], ["广告后台", "待接入", "ROI、投放、转化"]];
      const scopeText = payload?.canSeeAllUnitStores ? "总管 / 老板视角：经营单元全量" : "运营视角：我的店铺切片";
      return `<section class="unit-hero"><div><p class="eyebrow">STORE GROUP · ${s(payload?.scopeLabel || "经营单元")}</p><h2>${s(payload?.unitName || "家居生活店铺组")}</h2><p>${s(scopeText)} · 可见 ${s(payload?.visibleStoreCount || stores.length)} / ${s(payload?.allStoreCount || stores.length)} 家店铺</p></div><div class="unit-hero-side"><span>权限规则</span><strong>${s(payload?.scopeLabel || "店铺范围")}</strong><small>${s(payload?.permissionRule || "按当前账号店铺权限过滤数据")}</small></div></section>
      <section class="kpi-grid unit-metrics">${[["可见平台", payload?.platforms?.length || 0, (payload?.platforms || []).join(" / ") || "暂无"], ["可见店铺", payload?.visibleStoreCount || stores.length, "当前账号范围"], ["经营单元店铺", payload?.allStoreCount || stores.length, "总范围"], ["待接入系统", payload?.pendingSources?.length || 0, (payload?.pendingSources || []).join(" / ")]].map(([a,b,c]) => `<article class="card unit-metric-card"><h3>${s(a)}</h3><strong>${s(b)}</strong><span class="card-desc">${s(c)}</span></article>`).join("")}</section>
      <section class="page-section unit-store-section"><div class="section-header"><h3>${payload?.canSeeAllUnitStores ? "经营单元店铺范围" : "我的可见店铺"}</h3><span class="status-badge">${s(payload?.scopeLabel || "范围")}</span></div><p class="unit-scope-note">经营单元是共同业务空间；店铺权限决定商品、报表、预警和待办的可见范围。</p><div class="unit-store-table">${stores.map(storeRow).join("")}</div></section>
      <section class="page-section unit-store-section"><div class="section-header"><h3>数据接入状态</h3><span class="status-badge pending">可扩展</span></div><div class="unit-store-table">${sources.map(([system, status, usage]) => `<article class="unit-store-row"><strong>${s(system)}</strong><span>${s(status)}</span><em>${s(usage)}</em><small>经营单元数据来源</small></article>`).join("")}</div></section>`;
    },
  };
})();
