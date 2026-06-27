(function () {
  let activeId = null;
  let notice = "";
  let storeFilter = "";
  let cachedProducts = [];
  const s = (value) => AppShell.escape(value ?? "");

  function status(level) { return AppShell.statusClass(level); }
  function normalizeStoreName(item = {}) { return item.storeName || item.store || item.platform || "未绑定店铺"; }
  function normalizeProduct(item = {}) {
    return {
      ...item,
      id: item.id || item.productId || item.skuId || item.title || "PRODUCT",
      title: item.title || item.productTitle || item.shortName || item.id || "未命名商品",
      platform: item.platform || "平台",
      store: normalizeStoreName(item),
      imageLabel: item.imageLabel || "品",
      inventory: item.inventory ?? item.stock ?? "—",
      inventoryStatus: item.inventoryStatus || item.inventoryState || "库存待确认",
      inventoryLevel: item.inventoryLevel || "watch",
      price: item.price ?? "—",
      cost: item.cost ?? "—",
      grossMargin: item.grossMargin || item.margin || "—",
      afterSales: item.afterSales || item.afterSalesStatus || "正常",
      afterSalesLevel: item.afterSalesLevel || "good",
      suggestion: item.suggestion || item.reason || "根据导入数据生成经营判断。",
    };
  }
  async function loadProducts() {
    const payload = await AppApi.product();
    cachedProducts = Array.isArray(payload) ? payload.map(normalizeProduct) : [];
    return cachedProducts;
  }
  function visibleProducts() { return storeFilter ? cachedProducts.filter((item) => item.store === storeFilter || item.storeName === storeFilter || item.storeId === storeFilter) : cachedProducts; }
  function tagList(product) {
    const tags = [];
    if ((product.sourceDataVersions || []).length <= 1) tags.push("新入库");
    if (product.alertState?.activeAlertCount) tags.push(`${product.alertState.highestPriority || "中"}风险信号`);
    if (product.inventoryStatus && product.inventoryStatus !== "库存正常") tags.push(product.inventoryStatus);
    if (product.afterSales && product.afterSales !== "正常") tags.push("售后观察");
    if (product.grossMargin && product.grossMargin !== "—") tags.push(`毛利 ${product.grossMargin}`);
    return `<div class="action-chip-list">${(tags.length ? tags : ["待建立趋势线"]).map((tag) => `<span>${s(tag)}</span>`).join("")}</div>`;
  }
  function alertBadge(product) {
    const state = product.alertState || {};
    if (!state.activeAlertCount) return "";
    return `<div class="product-number-cell danger"><span>执行信号</span><strong>${s(state.activeAlertCount)}</strong><small>${s(state.highestPriority || "待处理")}</small></div>`;
  }
  function alertPanel(product) {
    const state = product.alertState || {};
    if (!state.activeAlertCount) return `<section class="page-section product-detail-section"><div class="section-header"><h3>商品标签</h3><span class="status-badge">观察</span></div><p>当前未进入执行任务，低风险信号已沉淀为商品标签。</p>${tagList(product)}</section>`;
    const latest = state.latestAlert || {};
    const evidence = (latest.evidence || []).map((item) => `<li>${s(item.label)}：${s(item.value)}</li>`).join("");
    return `<section class="page-section product-detail-section"><div class="section-header"><h3>报表触发信号</h3><span class="status-badge danger">${s(latest.priority || "中")}</span></div><p>${s(latest.alertType || "报表信号")} · ${s(latest.dataVersion || "数据版本")}</p><ul>${evidence}</ul></section>`;
  }
  function taskButton(item) {
    const task = window.AppTaskActions?.findOpenTask?.(item);
    return task ? `<button type="button" data-open-task="${s(task.id)}" class="ghost">查看任务</button><button type="button" data-task-report="${s(task.id)}">任务报告</button>` : `<button type="button" data-candidate-report="product:${s(item.id)}">查看详情</button>`;
  }
  function renderRow(product) {
    return `<article class="product-row"><div class="product-title-cell"><div class="product-thumb">${s(product.imageLabel || "品")}</div><div class="product-title-block"><strong>${s(product.title)}</strong><small>${s(product.id)} · ${s(product.platform)} · ${s(product.store || "店铺")}</small>${tagList(product)}</div></div><div class="product-metric-strip"><div class="product-number-cell ${status(product.inventoryLevel)}"><span>库存</span><strong>${s(product.inventory)}</strong><small>${s(product.inventoryStatus)}</small></div><div class="product-number-cell"><span>售价</span><strong>¥${s(product.price)}</strong><small>成本 ¥${s(product.cost)}</small></div><div class="product-number-cell"><span>毛利率</span><strong>${s(product.grossMargin)}</strong><small>清洗后数据</small></div><div class="product-number-cell ${status(product.afterSalesLevel)}"><span>售后</span><strong>${s(product.afterSales)}</strong><small>标签状态</small></div>${alertBadge(product)}</div><div class="product-actions"><button type="button" data-detail="${s(product.id)}">商品详情</button>${taskButton(product)}</div></article>`;
  }
  function renderDetail(product) {
    return `<section class="product-detail-hero"><div class="product-detail-main"><div class="product-thumb large">${s(product.imageLabel || "品")}</div><div><p class="eyebrow">PRODUCT ARCHIVE</p><h2>${s(product.title)}</h2><p>${s(product.platform)} · ${s(product.store)}</p>${product.link ? `<a href="${s(product.link)}" target="_blank" rel="noreferrer">${s(product.link)}</a>` : ""}</div></div><div class="product-detail-actions"><button type="button" data-back>返回商品列表</button>${taskButton(product)}</div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid product-detail-metrics"><article class="card"><h3>库存</h3><strong class="metric-${status(product.inventoryLevel)}">${s(product.inventory)}</strong><span class="card-desc">${s(product.inventoryStatus)}</span></article><article class="card"><h3>售价</h3><strong>¥${s(product.price)}</strong><span class="card-desc">成本 ¥${s(product.cost)}</span></article><article class="card"><h3>毛利率</h3><strong>${s(product.grossMargin)}</strong><span class="card-desc">清洗后数据</span></article><article class="card"><h3>售后</h3><strong class="metric-${status(product.afterSalesLevel)}">${s(product.afterSales)}</strong><span class="card-desc">标签状态</span></article></section>${alertPanel(product)}<section class="page-section product-detail-section"><div class="section-header"><h3>经营判断</h3><span class="status-badge">商品档案</span></div><p>${s(product.suggestion || "根据导入数据生成经营判断。")}</p></section>`;
  }
  function apiError(error) {
    return `<section class="product-toolbar"><div><p class="eyebrow">PRODUCT ARCHIVE · V11.15.2</p><h2>商品档案</h2></div></section><section class="page-section"><div class="section-header"><h3>接口异常</h3><span class="status-badge">无本地兜底</span></div><p>后端接口没有返回可用数据，页面已停止展示本地模拟业务内容。</p><strong>当前页面接口 ${s(error?.message || error || "请求失败")}</strong></section>`;
  }

  window.ProductPage = {
    route: "business-products",
    title: "商品档案",
    async render(ctx) {
      storeFilter = ctx?.state?.storeName || ctx?.state?.storeId || storeFilter || "";
      try { await loadProducts(); }
      catch (error) { return apiError(error); }
      if (activeId) {
        const product = cachedProducts.find((item) => item.id === activeId);
        if (product) return renderDetail(product);
        activeId = null;
      }
      const rows = visibleProducts();
      const empty = !rows.length;
      const filterText = storeFilter ? ` · ${storeFilter}` : "";
      return `<section class="product-toolbar"><div><p class="eyebrow">PRODUCT ARCHIVE · V11.15.2</p><h2>${empty ? "暂无商品数据" : `商品档案${s(filterText)}`}</h2><p>这里展示清洗后的商品列表、商品标签和基线状态；只有高风险高时效事项才进入任务栏。</p></div>${storeFilter ? `<button type="button" data-clear-filter>全部商品</button>` : ""}</section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="page-section product-list-section"><div class="section-header"><h3>商品列表</h3><span class="status-badge">${rows.length} 个商品</span></div><div class="product-card-list">${empty ? `<article class="dashboard-empty">暂无商品数据，请在报表模块导入商品、库存、订单或退款数据。</article>` : rows.map(renderRow).join("")}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-detail]", "click", (_, node) => { activeId = node.dataset.detail; notice = ""; AppRouter.schedule("product-detail"); });
      ctx.delegate("[data-back]", "click", () => { activeId = null; notice = ""; AppRouter.schedule("product-back"); });
      ctx.delegate("[data-clear-filter]", "click", () => { storeFilter = ""; AppRouter.schedule("product-filter-clear"); });
      ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask));
      ctx.delegate("[data-task-report]", "click", (_, node) => AppTaskActions.openTaskReport(node.dataset.taskReport));
      ctx.delegate("[data-candidate-report]", "click", (_, node) => { const [module, id] = node.dataset.candidateReport.split(":"); AppTaskActions.openCandidateReport(module, id); });
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();
