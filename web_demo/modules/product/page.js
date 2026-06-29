(function () {
  let activeId = null;
  let notice = "";
  let currentScope = {};
  let cachedProducts = [];
  const s = (value) => AppShell.escape(value ?? "");

  function status(level) { return AppShell.statusClass(level); }
  function normalizeStoreName(item = {}) { return item.storeName || item.store || item.platform || "未绑定店铺"; }
  function normalizeScope(state = {}) {
    if (Object.prototype.hasOwnProperty.call(state, "fromStore") && !state.fromStore && !state.storeId && !state.storeName) {
      clearScope();
      return currentScope;
    }
    if (state?.fromStore || state?.storeId || state?.storeName) {
      currentScope = { fromStore: Boolean(state.fromStore || state.storeId || state.storeName), storeId: state.storeId || "", storeName: state.storeName || "", platform: state.platform || "平台", productCount: Number(state.productCount || 0), storeWeightTag: state.storeWeightTag || "常规店铺", businessTags: Array.isArray(state.businessTags) ? state.businessTags : [], productRoleTags: Array.isArray(state.productRoleTags) ? state.productRoleTags : [], activeTaskCount: Number(state.activeTaskCount || 0) };
    }
    return currentScope;
  }
  function resolveActiveFromState(state = {}) {
    return state.productObjectId || state.objectId || state.archiveId || state.productId || state.activeId || "";
  }
  function clearScope() { currentScope = {}; activeId = null; }
  function scopedParams() { return currentScope?.fromStore ? { storeId: currentScope.storeId, storeName: currentScope.storeName } : {}; }
  function normalizeProduct(item = {}) {
    return { ...item, id: item.id || item.objectId || item.archiveId || item.productId || item.skuId || item.title || "PRODUCT", objectId: item.objectId || item.archiveId || item.id, productId: item.productId || item.rawProductId || item.id, title: item.title || item.productTitle || item.shortName || item.productId || item.id || "未命名商品", platform: item.platform || currentScope.platform || "平台", store: normalizeStoreName(item), imageLabel: item.imageLabel || "品", inventory: item.inventory ?? item.stock ?? "—", inventoryStatus: item.inventoryStatus || item.inventoryState || "库存待确认", inventoryLevel: item.inventoryLevel || "watch", price: item.avgOrderValue || item.price || "—", avgOrderValue: item.avgOrderValue || item.price || "—", paymentAmount: item.paymentAmount || "—", cost: item.costAmount || item.cost || "—", grossProfitAmount: item.grossProfitAmount || "—", grossMargin: item.grossMargin || item.margin || "—", roi: item.roi || "—", clickRate: item.clickRate || "—", conversionRate: item.conversionRate || "—", refundRate: item.refundRate || "—", adSpend: item.adSpend || "—", organicVisitors: item.organicVisitors || "—", paidVisitors: item.paidVisitors || "—", afterSales: item.afterSales || item.afterSalesStatus || "正常", afterSalesLevel: item.afterSalesLevel || "good", suggestion: item.suggestion || item.reason || "商品档案展示定位与指标事实，任务SOP在任务详情页处理。", productPosition: item.productPosition || {}, metricSections: Array.isArray(item.metricSections) ? item.metricSections : [], trafficSourceFacts: Array.isArray(item.trafficSourceFacts) ? item.trafficSourceFacts : [], taskHistorySummary: item.taskHistorySummary || {}, metricFactSummary: item.metricFactSummary || {} };
  }
  async function loadProducts() { const payload = await AppApi.product(scopedParams()); cachedProducts = Array.isArray(payload) ? payload.map(normalizeProduct) : []; return cachedProducts; }
  function sameProduct(product, id) { return id && [product.id, product.objectId, product.archiveId, product.productId, product.rawProductId, product.skuId].map(String).includes(String(id)); }
  function tagList(product) {
    const tags = [];
    if ((product.sourceDataVersions || []).length <= 1) tags.push("新入库");
    if (product.metricFactSummary?.factCount) tags.push(`事实 ${product.metricFactSummary.factCount}`);
    if (product.alertState?.activeAlertCount) tags.push(`${product.alertState.highestPriority || "中"}风险信号`);
    if (product.inventoryStatus && product.inventoryStatus !== "库存正常") tags.push(product.inventoryStatus);
    if (product.roi && product.roi !== "—") tags.push(`ROI ${product.roi}`);
    if (product.grossMargin && product.grossMargin !== "—") tags.push(`毛利 ${product.grossMargin}`);
    return `<div class="action-chip-list product-chip-list">${(tags.length ? tags : ["待建立趋势线"]).map((tag) => `<span>${s(tag)}</span>`).join("")}</div>`;
  }
  function smallTags(items = []) { const tags = Array.isArray(items) && items.length ? items : ["常规观察"]; return `<div class="product-scope-tags">${tags.map((tag) => `<span>${s(tag)}</span>`).join("")}</div>`; }
  function alertBadge(product) { const state = product.alertState || {}; if (!state.activeAlertCount) return ""; return `<div class="product-number-cell danger"><span>执行信号</span><strong>${s(state.activeAlertCount)}</strong><small>${s(state.highestPriority || "待处理")}</small></div>`; }
  function alertPanel(product) {
    const state = product.alertState || {};
    if (!state.activeAlertCount) return `<section class="page-section product-detail-section"><div class="section-header"><h3>商品标签</h3><span class="status-badge">观察</span></div><p>当前未进入执行任务，低风险信号已沉淀为商品标签。</p>${tagList(product)}</section>`;
    const latest = state.latestAlert || {};
    const evidence = (latest.evidence || []).map((item) => `<li>${s(item.label)}：${s(item.value)}</li>`).join("");
    return `<section class="page-section product-detail-section"><div class="section-header"><h3>报表触发信号</h3><span class="status-badge danger">${s(latest.priority || "中")}</span></div><p>${s(latest.alertType || "报表信号")} · ${s(latest.dataVersion || "数据版本")}</p><ul>${evidence}</ul></section>`;
  }
  function taskButton(item) { const task = window.AppTaskActions?.findOpenTask?.(item); return task ? `<button type="button" data-open-task="${s(task.id)}" class="ghost">查看任务</button><button type="button" data-task-report="${s(task.id)}">任务报告</button>` : `<button type="button" data-candidate-module="product" data-candidate-id="${s(item.id)}">任务证据</button>`; }
  function scopeHero(rows = []) {
    if (!currentScope?.fromStore) return `<section class="product-archive-hero"><div><p class="eyebrow">PRODUCT ARCHIVE · V12.12</p><h2>商品档案</h2><p>展示当前账号可见的商品定位、系统编码和指标事实。</p></div><div class="product-scope-panel"><span>商品</span><strong>${rows.length}</strong><small>全局商品档案</small></div></section>`;
    return `<section class="product-archive-hero scoped"><div><p class="eyebrow">STORE PRODUCT ARCHIVE · V12.12</p><h2>${s(currentScope.storeName || "店铺商品档案")}</h2><p>${s(currentScope.platform || "平台")} · 当前店铺 ${rows.length || currentScope.productCount || 0} 个商品 · 店铺级商品档案</p>${smallTags([currentScope.storeWeightTag, ...(currentScope.businessTags || [])])}</div><div class="product-scope-panel"><span>执行任务</span><strong>${s(currentScope.activeTaskCount || 0)}</strong><small>${s((currentScope.productRoleTags || [])[0] || "商品状态")}</small><button type="button" class="secondary" data-clear-filter>全部商品</button></div></section>`;
  }
  function renderRow(product) { return `<article class="product-row"><div class="product-title-cell"><div class="product-thumb">${s(product.imageLabel || "品")}</div><div class="product-title-block"><strong>${s(product.title)}</strong><small>${s(product.productId)} · ${s(product.platform)} · ${s(product.store || "店铺")}</small>${tagList(product)}</div></div><div class="product-metric-strip"><div class="product-number-cell ${status(product.inventoryLevel)}"><span>库存</span><strong>${s(product.inventory)}</strong><small>${s(product.inventoryStatus)}</small></div><div class="product-number-cell"><span>ROI</span><strong>${s(product.roi)}</strong><small>广告投产</small></div><div class="product-number-cell"><span>转化率</span><strong>${s(product.conversionRate)}</strong><small>支付转化</small></div><div class="product-number-cell ${status(product.afterSalesLevel)}"><span>退款率</span><strong>${s(product.refundRate)}</strong><small>${s(product.afterSales)}</small></div>${alertBadge(product)}</div><div class="product-actions"><button type="button" data-detail="${s(product.id)}">商品详情</button>${taskButton(product)}</div></article>`; }
  function renderPosition(product) {
    const pos = product.productPosition || {};
    const rows = [["系统店铺编码", pos.systemStoreCode], ["系统SPU编码", pos.systemSpuCode], ["系统LINK编码", pos.systemLinkCode], ["系统SKU编码", pos.systemSkuCode], ["平台", pos.platform || product.platform], ["店铺", pos.storeName || product.store], ["商品ID", pos.productId || product.productId], ["SKU ID", pos.skuId || product.skuId], ["ERP编码", pos.erpProductCode || product.erpProductCode], ["商品链接", pos.productLink || product.productLink || product.link]].filter(([, value]) => value && value !== "—");
    return `<section class="page-section product-detail-section"><div class="section-header"><h3>商品定位</h3><span class="status-badge">系统编码</span></div><div class="product-position-grid">${rows.map(([label, value]) => `<div><span>${s(label)}</span><strong>${s(value)}</strong></div>`).join("")}</div></section>`;
  }
  function renderMetricSections(product) {
    const sections = (product.metricSections || []).filter((section) => Array.isArray(section.items) && section.items.length);
    if (!sections.length) return `<section class="page-section product-detail-section"><div class="section-header"><h3>指标事实</h3><span class="status-badge">待入库</span></div><p>当前商品还没有可展示的独立指标事实，请先完成报表导入。</p></section>`;
    return `<section class="page-section product-detail-section"><div class="section-header"><h3>指标事实</h3><span class="status-badge">${s(product.metricFactSummary?.factCount || 0)} 条</span></div><div class="product-fact-section-list">${sections.map((section) => `<article class="product-fact-section"><h4>${s(section.title)}</h4><div class="product-fact-grid">${section.items.map((item) => `<div><span>${s(item.metricName)}</span><strong>${s(item.displayValue)}</strong><small>${s(item.sourceSheet || "事实表")}${item.statDate ? ` · ${s(item.statDate)}` : ""}</small></div>`).join("")}</div></article>`).join("")}</div></section>`;
  }
  function renderTrafficFacts(product) { const rows = product.trafficSourceFacts || []; if (!rows.length) return ""; return `<section class="page-section product-detail-section"><div class="section-header"><h3>流量来源</h3><span class="status-badge">${rows.length} 类</span></div><div class="product-traffic-list">${rows.map((item) => `<article><strong>${s(item.trafficSource)}</strong><span>访客 ${s(item.visitorCount || "—")}</span><span>点击率 ${s(item.clickRate || "—")}</span><span>转化 ${s(item.conversionRate || "—")}</span><span>ROI ${s(item.roi || "—")}</span></article>`).join("")}</div></section>`; }
  function renderTaskSummary(product) { const summary = product.taskHistorySummary || {}; return `<section class="page-section product-detail-section"><div class="section-header"><h3>任务历史摘要</h3><span class="status-badge">${summary.hasActiveTask ? "有未完成任务" : "无未完成任务"}</span></div><p>${s(summary.summary || "商品页只显示任务摘要，完整SOP在任务详情页查看。")}</p><div class="product-position-grid compact"><div><span>任务次数</span><strong>${s(summary.taskCount || 0)}</strong></div><div><span>当前任务</span><strong>${s(summary.activeTaskStatus || "—")}</strong></div><div><span>最近完成</span><strong>${s(summary.completedTaskStatus || "—")}</strong></div></div></section>`; }
  function renderDetail(product) { return `<section class="product-detail-hero"><div class="product-detail-main"><div class="product-thumb large">${s(product.imageLabel || "品")}</div><div><p class="eyebrow">PRODUCT ARCHIVE · V12.12</p><h2>${s(product.title)}</h2><p>${s(product.platform)} · ${s(product.store)} · ${s(product.productId)}</p>${product.link || product.productLink ? `<a href="${s(product.link || product.productLink)}" target="_blank" rel="noreferrer">${s(product.link || product.productLink)}</a>` : ""}</div></div><div class="product-detail-actions"><button type="button" data-back>返回商品列表</button>${taskButton(product)}</div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid product-detail-metrics"><article class="card"><h3>库存</h3><strong class="metric-${status(product.inventoryLevel)}">${s(product.inventory)}</strong><span class="card-desc">${s(product.inventoryStatus)}</span></article><article class="card"><h3>支付金额</h3><strong>${s(product.paymentAmount)}</strong><span class="card-desc">客单价 ${s(product.avgOrderValue)}</span></article><article class="card"><h3>ROI</h3><strong>${s(product.roi)}</strong><span class="card-desc">广告消耗 ${s(product.adSpend)}</span></article><article class="card"><h3>毛利率</h3><strong>${s(product.grossMargin)}</strong><span class="card-desc">毛利 ${s(product.grossProfitAmount)}</span></article></section>${renderPosition(product)}${renderMetricSections(product)}${renderTrafficFacts(product)}${renderTaskSummary(product)}${alertPanel(product)}<section class="page-section product-detail-section"><div class="section-header"><h3>商品页边界</h3><span class="status-badge">资产定位</span></div><p>商品页展示商品是谁、在哪里、有哪些指标事实、历史任务摘要。完整交叉验证、RAG/LLM SOP 和提交证明在任务详情页处理。</p></section>`; }
  function apiError(error) { return `<section class="product-toolbar"><div><p class="eyebrow">PRODUCT ARCHIVE · V12.12</p><h2>商品档案</h2></div></section><section class="page-section"><div class="section-header"><h3>接口异常</h3><span class="status-badge">无本地兜底</span></div><p>后端接口没有返回可用数据，页面已停止展示本地模拟业务内容。</p><strong>当前页面接口 ${s(error?.message || error || "请求失败")}</strong></section>`; }

  window.ProductPage = {
    route: "business-products",
    title: "商品档案",
    async render(ctx) {
      const state = ctx?.state || {};
      normalizeScope(state);
      const requested = resolveActiveFromState(state);
      if (requested) activeId = requested;
      try { await loadProducts(); } catch (error) { return apiError(error); }
      if (activeId) {
        const product = cachedProducts.find((item) => sameProduct(item, activeId));
        if (product) return renderDetail(product);
        notice = `未找到商品 ${activeId}，已返回商品列表。`;
        activeId = null;
      }
      const rows = cachedProducts;
      const empty = !rows.length;
      return `${scopeHero(rows)}${notice ? AppShell.notice("操作结果", notice) : ""}<section class="page-section product-list-section"><div class="section-header"><h3>${currentScope?.fromStore ? "店铺商品列表" : "商品列表"}</h3><span class="status-badge">${rows.length} 个商品</span></div><div class="product-card-list">${empty ? `<article class="dashboard-empty">暂无商品数据，请在报表模块导入商品、库存、订单或退款数据。</article>` : rows.map(renderRow).join("")}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-detail]", "click", (_, node) => { activeId = node.dataset.detail; notice = ""; AppRouter.schedule("product-detail"); });
      ctx.delegate("[data-back]", "click", () => { activeId = null; notice = ""; AppRouter.schedule("product-back"); });
      ctx.delegate("[data-clear-filter]", "click", () => { clearScope(); AppRouter.schedule("product-filter-clear", { fromStore: false }); });
      ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask));
      ctx.delegate("[data-task-report]", "click", (_, node) => AppTaskActions.openTaskReport(node.dataset.taskReport));
      ctx.delegate("[data-candidate-id]", "click", (_, node) => AppTaskActions.openCandidateReport(node.dataset.candidateModule, node.dataset.candidateId));
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();
