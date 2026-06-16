(function () {
  let activeId = null;
  let notice = "";
  const products = () => AppMockData.products;
  const s = (value) => AppShell.escape(value);
  function status(level) { return AppShell.statusClass(level); }
  function renderRow(product) {
    const existed = AppTaskStore.findOpenTask(AppTaskActions.productIdentity(product));
    return `<article class="product-row"><div class="product-title-cell"><div class="product-thumb">${s(product.imageLabel)}</div><div class="product-title-block"><strong>${s(product.title)}</strong><small>${s(product.id)} · <a href="${s(product.link)}" target="_blank" rel="noreferrer">查看商品链接</a></small><span>${s(product.platform)} · ${s(product.store)}</span></div></div><div class="product-metric-strip"><div class="product-number-cell ${status(product.inventoryLevel)}"><span>库存</span><strong>${s(product.inventory)}</strong><small>${s(product.inventoryStatus)}</small></div><div class="product-number-cell"><span>售价</span><strong>¥${s(product.price)}</strong><small>成本 ¥${s(product.cost)}</small></div><div class="product-number-cell"><span>毛利率</span><strong>${s(product.grossMargin)}</strong><small>活动需复核</small></div><div class="product-number-cell ${status(product.afterSalesLevel)}"><span>售后</span><strong>${s(product.afterSales)}</strong><small>售后状态</small></div></div><div class="product-actions"><button type="button" data-detail="${s(product.id)}">详情</button><button type="button" data-copy="${s(product.id)}">复制链接</button><button type="button" data-task="${s(product.id)}" class="${existed ? "ghost" : ""}">${existed ? "已在待办" : "加入待办"}</button></div></article>`;
  }
  function renderDetail(product) {
    return `<section class="product-detail-hero"><div class="product-detail-main"><div class="product-thumb large">${s(product.imageLabel)}</div><div><p class="eyebrow">PRODUCT DETAIL</p><h2>${s(product.title)}</h2><p>${s(product.platform)} · ${s(product.store)}</p><a href="${s(product.link)}" target="_blank" rel="noreferrer">${s(product.link)}</a></div></div><div class="product-detail-actions"><button type="button" data-back>返回商品列表</button><button type="button" data-copy="${s(product.id)}">复制链接</button><button type="button" data-task="${s(product.id)}">加入待办</button></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="kpi-grid product-detail-metrics"><article class="card"><h3>库存</h3><strong class="metric-${status(product.inventoryLevel)}">${s(product.inventory)}</strong><span class="card-desc">${s(product.inventoryStatus)}</span></article><article class="card"><h3>售价</h3><strong>¥${s(product.price)}</strong><span class="card-desc">成本 ¥${s(product.cost)}</span></article><article class="card"><h3>毛利率</h3><strong>${s(product.grossMargin)}</strong><span class="card-desc">活动价需复核</span></article><article class="card"><h3>售后</h3><strong class="metric-${status(product.afterSalesLevel)}">${s(product.afterSales)}</strong><span class="card-desc">来自 CRM 报表</span></article></section><section class="page-section product-detail-section"><div class="section-header"><h3>处理建议</h3><span class="status-badge">经营判断</span></div><p>${s(product.suggestion)}</p></section>`;
  }
  window.ProductPage = {
    route: "business-products",
    title: "商品",
    render() {
      if (activeId) { const product = products().find((item) => item.id === activeId); if (product) return renderDetail(product); activeId = null; }
      return `<section class="product-toolbar"><div><p class="eyebrow">PRODUCT LIST</p><h2>商品经营列表</h2><p>按平台、店铺和状态查看商品；任务创建进入服务端任务池，不直接改店铺数据。</p></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="page-section product-list-section"><div class="section-header"><h3>商品列表</h3><span class="status-badge">${products().length} 个商品</span></div><div class="product-card-list">${products().map(renderRow).join("")}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-detail]", "click", (_, node) => { activeId = node.dataset.detail; notice = ""; AppRouter.schedule("product-detail"); });
      ctx.delegate("[data-back]", "click", () => { activeId = null; notice = ""; AppRouter.schedule("product-back"); });
      ctx.delegate("[data-task]", "click", async (_, node) => { notice = "任务提交中..."; AppRouter.schedule("product-task-start"); const result = await AppTaskActions.createProductTask(node.dataset.task); notice = result?.message || "任务已处理。"; AppRouter.schedule("product-task"); });
      ctx.delegate("[data-copy]", "click", async (_, node) => { const product = products().find((item) => item.id === node.dataset.copy); if (!product) return; try { await navigator.clipboard.writeText(product.link); notice = `${product.shortName}商品链接已复制。`; } catch { notice = product.link; } AppRouter.schedule("product-copy"); });
      ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store")));
    },
  };
})();
