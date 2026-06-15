const productManagerPayload = {
  filters: ["全部平台", "全部店铺", "库存异常", "售后敏感", "毛利偏低"],
  products: [
    {
      id: "P001",
      shortName: "遮阳伞",
      title: "遮阳伞户外便携防晒防紫外线晴雨两用",
      platform: "淘宝",
      store: "家居生活主店",
      imageLabel: "伞",
      link: "https://shop.example.com/products/P001",
      inventory: 200,
      inventoryStatus: "库存偏高",
      inventoryLevel: "warning",
      price: 39,
      cost: 18,
      grossMargin: "53%",
      afterSales: "正常",
      afterSalesLevel: "good",
      suggestion: "库存偏高但订单少，先做自然流量测试或清货活动测算。",
    },
    {
      id: "P002",
      shortName: "厨房置物架",
      title: "厨房置物架免打孔收纳架壁挂多层家用置物架",
      platform: "拼多多",
      store: "家居百货店",
      imageLabel: "架",
      link: "https://shop.example.com/products/P002",
      inventory: 120,
      inventoryStatus: "正常",
      inventoryLevel: "good",
      price: 49,
      cost: 22,
      grossMargin: "55%",
      afterSales: "退款偏高",
      afterSalesLevel: "warning",
      suggestion: "补充尺寸参照图和安装说明，降低安装预期偏差。",
    },
    {
      id: "P003",
      shortName: "护腰坐垫",
      title: "护腰坐垫久坐办公室靠垫人体工学支撑款",
      platform: "抖音小店",
      store: "家居好物号",
      imageLabel: "垫",
      link: "https://shop.example.com/products/P003",
      inventory: 80,
      inventoryStatus: "待补货",
      inventoryLevel: "danger",
      price: 69,
      cost: 35,
      grossMargin: "49%",
      afterSales: "售后敏感",
      afterSalesLevel: "warning",
      suggestion: "复查材质、支撑感描述和客服承诺，售后归因完成前不建议放量。",
    },
    {
      id: "P004",
      shortName: "收纳盒",
      title: "透明收纳盒衣柜整理箱家用大容量防尘款",
      platform: "淘宝",
      store: "家居生活主店",
      imageLabel: "盒",
      link: "https://shop.example.com/products/P004",
      inventory: 46,
      inventoryStatus: "库存告急",
      inventoryLevel: "danger",
      price: 29,
      cost: 13,
      grossMargin: "55%",
      afterSales: "正常",
      afterSalesLevel: "good",
      suggestion: "库存低于安全线，先确认补货周期和主推节奏。",
    },
  ],
};

let activeProductId = null;
let productNotice = "";

function isProductRoute() {
  return location.hash.replace("#", "") === "business-products" || document.querySelector('.nav a[data-route="business-products"]')?.classList.contains("active");
}

function productStatusClass(level) {
  return level === "danger" ? "danger" : level === "warning" ? "warning" : "good";
}

function productNoticeMarkup() {
  if (!productNotice) return "";
  return `<section class="product-notice"><strong>操作结果</strong><span>${productNotice}</span></section>`;
}

function renderProductManager() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || !isProductRoute()) return;
  activeProductId = null;
  title.textContent = "商品";
  appView.innerHTML = `<section class="product-toolbar">
    <div>
      <p class="eyebrow">PRODUCT LIST</p>
      <h2>商品经营列表</h2>
      <p>按平台、店铺、标题、主图和链接管理商品，库存和售后状态直接标在对应字段上。</p>
    </div>
    <div class="product-filter-row">
      ${productManagerPayload.filters.map((filter, index) => `<button type="button" class="${index === 0 ? "active" : ""}">${filter}</button>`).join("")}
    </div>
  </section>
  ${productNoticeMarkup()}
  <section class="page-section product-list-section">
    <div class="section-header">
      <h3>商品列表</h3>
      <span class="status-badge">${productManagerPayload.products.length} 个商品</span>
    </div>
    <div class="product-list-table">
      <div class="product-list-head">
        <span>商品</span><span>平台 / 店铺</span><span>库存</span><span>售价</span><span>毛利率</span><span>售后</span><span>操作</span>
      </div>
      ${productManagerPayload.products.map((product) => `<article class="product-row">
        <div class="product-title-cell">
          <div class="product-thumb">${product.imageLabel}</div>
          <div>
            <strong>${product.title}</strong>
            <small>${product.id} · <a href="${product.link}" target="_blank" rel="noreferrer">查看商品链接</a></small>
          </div>
        </div>
        <div class="product-store-cell"><strong>${product.platform}</strong><small>${product.store}</small></div>
        <div class="product-number-cell ${productStatusClass(product.inventoryLevel)}"><strong>${product.inventory}</strong><small>${product.inventoryStatus}</small></div>
        <div class="product-number-cell"><strong>¥${product.price}</strong><small>成本 ¥${product.cost}</small></div>
        <div class="product-number-cell"><strong>${product.grossMargin}</strong><small>活动需复核</small></div>
        <div class="product-number-cell ${productStatusClass(product.afterSalesLevel)}"><strong>${product.afterSales}</strong><small>售后状态</small></div>
        <div class="product-actions">
          <button type="button" data-product-detail="${product.id}">详情</button>
          <button type="button" data-product-copy="${product.id}">复制链接</button>
          <button type="button" data-product-report="${product.id}">商品报表</button>
        </div>
      </article>`).join("")}
    </div>
  </section>`;
  bindProductButtons();
}

function renderProductDetail(productId) {
  const product = productManagerPayload.products.find((item) => item.id === productId);
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!product || !appView || !title) return;
  activeProductId = productId;
  title.textContent = product.shortName;
  appView.innerHTML = `<section class="product-detail-hero">
    <div class="product-detail-main">
      <div class="product-thumb large">${product.imageLabel}</div>
      <div>
        <p class="eyebrow">PRODUCT DETAIL</p>
        <h2>${product.title}</h2>
        <p>${product.platform} · ${product.store}</p>
        <a href="${product.link}" target="_blank" rel="noreferrer">${product.link}</a>
      </div>
    </div>
    <div class="product-detail-actions">
      <button type="button" data-product-back>返回商品列表</button>
      <button type="button" data-product-copy="${product.id}">复制链接</button>
      <button type="button" data-product-report="${product.id}">商品报表</button>
    </div>
  </section>
  ${productNoticeMarkup()}
  <section class="kpi-grid product-detail-metrics">
    <article class="card"><h3>库存</h3><strong class="metric-${productStatusClass(product.inventoryLevel)}">${product.inventory}</strong><span class="card-desc">${product.inventoryStatus}</span></article>
    <article class="card"><h3>售价</h3><strong>¥${product.price}</strong><span class="card-desc">成本 ¥${product.cost}</span></article>
    <article class="card"><h3>毛利率</h3><strong>${product.grossMargin}</strong><span class="card-desc">活动价需复核</span></article>
    <article class="card"><h3>售后</h3><strong class="metric-${productStatusClass(product.afterSalesLevel)}">${product.afterSales}</strong><span class="card-desc">来自 CRM 报表</span></article>
  </section>
  <section class="page-section product-detail-section">
    <div class="section-header"><h3>处理建议</h3><span class="status-badge">经营判断</span></div>
    <p>${product.suggestion}</p>
  </section>`;
  bindProductButtons();
}

function bindProductButtons() {
  document.querySelectorAll("[data-product-detail]").forEach((button) => {
    button.addEventListener("click", () => {
      productNotice = "";
      renderProductDetail(button.dataset.productDetail);
    });
  });
  document.querySelectorAll("[data-product-back]").forEach((button) => {
    button.addEventListener("click", () => {
      activeProductId = null;
      productNotice = "";
      renderProductManager();
    });
  });
  document.querySelectorAll("[data-product-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const product = productManagerPayload.products.find((item) => item.id === button.dataset.productCopy);
      if (!product) return;
      try {
        await navigator.clipboard.writeText(product.link);
        productNotice = `${product.shortName}商品链接已复制。`;
      } catch {
        productNotice = `${product.shortName}商品链接：${product.link}`;
      }
      if (activeProductId) renderProductDetail(activeProductId);
      else renderProductManager();
    });
  });
  document.querySelectorAll("[data-product-report]").forEach((button) => {
    button.addEventListener("click", () => {
      productNotice = "已跳转到商品报表，可查看商品明细数据。";
      location.hash = "data-check";
      setTimeout(() => {
        document.querySelector('[data-report-id="products"]')?.dispatchEvent(new Event("click"));
      }, 180);
    });
  });
}

function scheduleProductPatch() {
  setTimeout(() => {
    if (!isProductRoute()) return;
    if (activeProductId) renderProductDetail(activeProductId);
    else renderProductManager();
  }, 0);
  setTimeout(() => {
    if (!isProductRoute()) return;
    if (!document.querySelector(".product-toolbar") && !document.querySelector(".product-detail-hero")) renderProductManager();
  }, 160);
}

const productObserver = new MutationObserver(() => {
  if (isProductRoute()) scheduleProductPatch();
});

productObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("hashchange", () => {
  activeProductId = null;
  productNotice = "";
  scheduleProductPatch();
});
window.addEventListener("load", scheduleProductPatch);
scheduleProductPatch();
