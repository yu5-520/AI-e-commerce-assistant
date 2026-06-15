const competitorManagerPayload = {
  competitors: [
    {
      id: "C001",
      targetProduct: "厨房置物架",
      title: "厨房置物架免打孔多层收纳架壁挂家用加厚款",
      platform: "拼多多",
      store: "家居收纳旗舰店",
      imageLabel: "架",
      link: "https://shop.example.com/competitors/C001",
      price: 39,
      pricePosition: "低于市场价",
      monthlySales: "3200+",
      rating: "4.7",
      badReview: "安装困难 / 尺寸不符",
      opportunity: "补安装图和尺寸参照图",
      status: "机会",
      statusLevel: "good",
      suggestion: "价格低但差评集中在安装和尺寸，优先补充详情页说明，不建议直接跟价。",
    },
    {
      id: "C002",
      targetProduct: "厨房置物架",
      title: "厨房台面置物架多层调料架免安装大容量收纳架",
      platform: "淘宝",
      store: "厨房好物店",
      imageLabel: "厨",
      link: "https://shop.example.com/competitors/C002",
      price: 59,
      pricePosition: "高于市场价",
      monthlySales: "1800+",
      rating: "4.8",
      badReview: "物流破损 / 承重不足",
      opportunity: "强化包装和承重卖点",
      status: "待观察",
      statusLevel: "warning",
      suggestion: "售价更高但评分稳定，可对标包装和承重表达。",
    },
    {
      id: "C003",
      targetProduct: "厨房置物架",
      title: "厨房置物架落地多层收纳架锅具微波炉架",
      platform: "抖音小店",
      store: "厨房整理研究所",
      imageLabel: "锅",
      link: "https://shop.example.com/competitors/C003",
      price: 79,
      pricePosition: "高于市场价",
      monthlySales: "860+",
      rating: "4.6",
      badReview: "安装咨询较多 / 稳定性一般",
      opportunity: "用视频说明安装流程",
      status: "风险",
      statusLevel: "danger",
      suggestion: "客单价高但安装门槛明显，不能直接套用其卖点。",
    },
    {
      id: "C004",
      targetProduct: "厨房置物架",
      title: "免打孔厨房挂架墙上置物架调料收纳架",
      platform: "拼多多",
      store: "百货低价仓",
      imageLabel: "挂",
      link: "https://shop.example.com/competitors/C004",
      price: 29,
      pricePosition: "低于市场价",
      monthlySales: "5200+",
      rating: "4.4",
      badReview: "材质薄 / 掉落",
      opportunity: "避开低质低价竞争",
      status: "风险",
      statusLevel: "danger",
      suggestion: "低价高销量但质量差评明显，不适合盲目跟价。",
    },
    {
      id: "C005",
      targetProduct: "遮阳伞",
      title: "防晒遮阳伞黑胶晴雨两用便携防紫外线太阳伞",
      platform: "淘宝",
      store: "夏日出行旗舰店",
      imageLabel: "伞",
      link: "https://shop.example.com/competitors/C005",
      price: 45,
      pricePosition: "接近市场价",
      monthlySales: "4100+",
      rating: "4.8",
      badReview: "伞骨不稳 / 收纳袋小",
      opportunity: "突出伞骨和收纳体验",
      status: "机会",
      statusLevel: "good",
      suggestion: "价格接近市场，差评集中在结构稳定和收纳，可补强主图卖点。",
    },
    {
      id: "C006",
      targetProduct: "护腰坐垫",
      title: "久坐护腰坐垫办公室人体工学靠垫座椅支撑垫",
      platform: "抖音小店",
      store: "办公舒适生活馆",
      imageLabel: "垫",
      link: "https://shop.example.com/competitors/C006",
      price: 89,
      pricePosition: "高于市场价",
      monthlySales: "1200+",
      rating: "4.5",
      badReview: "支撑不足 / 材质偏软",
      opportunity: "补实测支撑图和材质说明",
      status: "风险",
      statusLevel: "danger",
      suggestion: "用户对支撑感预期高，详情页不能只写舒适，要给材质和支撑证据。",
    },
    {
      id: "C007",
      targetProduct: "收纳盒",
      title: "透明收纳盒衣柜整理箱可叠加家用塑料储物盒",
      platform: "拼多多",
      store: "家庭收纳仓",
      imageLabel: "盒",
      link: "https://shop.example.com/competitors/C007",
      price: 25,
      pricePosition: "低于市场价",
      monthlySales: "6800+",
      rating: "4.6",
      badReview: "尺寸偏差 / 盖子松",
      opportunity: "补尺寸对照和盖子细节",
      status: "机会",
      statusLevel: "good",
      suggestion: "销量高但尺寸争议多，适合作为尺寸说明优化参考。",
    },
    {
      id: "C008",
      targetProduct: "收纳盒",
      title: "加厚收纳箱透明衣物整理箱大容量带轮储物箱",
      platform: "淘宝",
      store: "品质家居馆",
      imageLabel: "箱",
      link: "https://shop.example.com/competitors/C008",
      price: 49,
      pricePosition: "高于市场价",
      monthlySales: "950+",
      rating: "4.9",
      badReview: "物流压坏 / 发货慢",
      opportunity: "对标品质表达，避开物流承诺过度",
      status: "待观察",
      statusLevel: "warning",
      suggestion: "评分高但供应链要求更高，适合观察品质定位，不适合马上跟款。",
    },
  ],
};

let activeCompetitorId = null;
let competitorNotice = "";
let openCompetitorFilter = null;
let competitorRenderScheduled = false;
const competitorFilters = {
  platform: "全部平台",
  target: "全部商品",
  status: "全部状态",
  search: "",
};

function isCompetitorRoute() {
  return location.hash.replace("#", "") === "business-competitors" || document.querySelector('.nav a[data-route="business-competitors"]')?.classList.contains("active");
}

function competitorStatusClass(level) {
  return level === "danger" ? "danger" : level === "warning" ? "warning" : "good";
}

function competitorNoticeMarkup() {
  if (!competitorNotice) return "";
  return `<section class="competitor-notice"><strong>操作结果</strong><span>${competitorNotice}</span></section>`;
}

function competitorFilterOptions(type) {
  if (type === "platform") return ["全部平台", ...new Set(competitorManagerPayload.competitors.map((item) => item.platform))];
  if (type === "target") return ["全部商品", ...new Set(competitorManagerPayload.competitors.map((item) => item.targetProduct))];
  return ["全部状态", "机会", "风险", "待观察"];
}

function renderCompetitorFilter(type, label) {
  const value = competitorFilters[type];
  const isOpen = openCompetitorFilter === type;
  return `<div class="competitor-filter-menu ${isOpen ? "open" : ""}">
    <button type="button" data-competitor-filter-toggle="${type}">${label}：${value} <span>⌄</span></button>
    <div class="competitor-filter-options">
      ${competitorFilterOptions(type).map((option) => `<button type="button" class="${option === value ? "selected" : ""}" data-competitor-filter-value="${type}:${option}">${option}</button>`).join("")}
    </div>
  </div>`;
}

function competitorMatchesFilters(item) {
  if (competitorFilters.platform !== "全部平台" && item.platform !== competitorFilters.platform) return false;
  if (competitorFilters.target !== "全部商品" && item.targetProduct !== competitorFilters.target) return false;
  if (competitorFilters.status !== "全部状态" && item.status !== competitorFilters.status) return false;
  const keyword = competitorFilters.search.trim().toLowerCase();
  if (!keyword) return true;
  return [item.id, item.targetProduct, item.title, item.platform, item.store, item.pricePosition, item.badReview, item.opportunity, item.status]
    .join(" ")
    .toLowerCase()
    .includes(keyword);
}

function filteredCompetitors() {
  return competitorManagerPayload.competitors.filter(competitorMatchesFilters);
}

function competitorFilterSummary(count) {
  const active = [
    competitorFilters.platform !== "全部平台" ? competitorFilters.platform : null,
    competitorFilters.target !== "全部商品" ? competitorFilters.target : null,
    competitorFilters.status !== "全部状态" ? competitorFilters.status : null,
    competitorFilters.search.trim() ? `搜索：${competitorFilters.search.trim()}` : null,
  ].filter(Boolean);
  return active.length ? `${count} 个竞品 · ${active.join(" / ")}` : `${count} 个竞品`;
}

function renderCompetitorRow(item) {
  return `<article class="competitor-row">
    <div class="competitor-title-cell">
      <div class="competitor-thumb">${item.imageLabel}</div>
      <div class="competitor-title-block">
        <strong>${item.title}</strong>
        <small>${item.id} · 对标 ${item.targetProduct} · <a href="${item.link}" target="_blank" rel="noreferrer">查看竞品链接</a></small>
        <span>${item.platform} · ${item.store}</span>
      </div>
    </div>
    <div class="competitor-metric-strip">
      <div class="competitor-number-cell ${competitorStatusClass(item.statusLevel)}"><span>价格</span><strong>¥${item.price}</strong><small>${item.pricePosition}</small></div>
      <div class="competitor-number-cell"><span>月销</span><strong>${item.monthlySales}</strong><small>参考销量</small></div>
      <div class="competitor-number-cell"><span>评分</span><strong>${item.rating}</strong><small>用户反馈</small></div>
      <div class="competitor-number-cell ${competitorStatusClass(item.statusLevel)}"><span>状态</span><strong>${item.status}</strong><small>${item.badReview}</small></div>
    </div>
    <div class="competitor-opportunity">
      <span>机会点</span>
      <strong>${item.opportunity}</strong>
    </div>
    <div class="competitor-actions">
      <button type="button" data-competitor-detail="${item.id}">详情</button>
      <button type="button" data-competitor-copy="${item.id}">复制链接</button>
      <button type="button" data-competitor-watch="${item.id}">加入观察</button>
    </div>
  </article>`;
}

function renderCompetitorManager() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || !isCompetitorRoute()) return;
  const competitors = filteredCompetitors();
  activeCompetitorId = null;
  title.textContent = "竞品";
  appView.innerHTML = `<section class="competitor-toolbar">
    <div>
      <p class="eyebrow">COMPETITOR LIST</p>
      <h2>竞品观察列表</h2>
      <p>按平台、对标商品和状态筛选竞品；价格、销量、评分、差评点和机会点直接展示在卡片上。</p>
    </div>
    <div class="competitor-filter-row">
      ${renderCompetitorFilter("platform", "平台")}
      ${renderCompetitorFilter("target", "对标商品")}
      ${renderCompetitorFilter("status", "状态")}
      <label class="competitor-search"><input type="search" value="${competitorFilters.search}" placeholder="搜索竞品 / 差评" data-competitor-search /></label>
    </div>
  </section>
  ${competitorNoticeMarkup()}
  <section class="page-section competitor-list-section">
    <div class="section-header">
      <h3>竞品列表</h3>
      <span class="status-badge">${competitorFilterSummary(competitors.length)}</span>
    </div>
    <div class="competitor-card-list">
      ${competitors.length ? competitors.map(renderCompetitorRow).join("") : `<div class="competitor-empty">当前筛选条件下没有竞品。</div>`}
    </div>
  </section>`;
  bindCompetitorButtons();
}

function renderCompetitorDetail(competitorId) {
  const item = competitorManagerPayload.competitors.find((competitor) => competitor.id === competitorId);
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!item || !appView || !title) return;
  activeCompetitorId = competitorId;
  openCompetitorFilter = null;
  title.textContent = item.targetProduct;
  appView.innerHTML = `<section class="competitor-detail-hero">
    <div class="competitor-detail-main">
      <div class="competitor-thumb large">${item.imageLabel}</div>
      <div>
        <p class="eyebrow">COMPETITOR DETAIL</p>
        <h2>${item.title}</h2>
        <p>${item.platform} · ${item.store} · 对标 ${item.targetProduct}</p>
        <a href="${item.link}" target="_blank" rel="noreferrer">${item.link}</a>
      </div>
    </div>
    <div class="competitor-detail-actions">
      <button type="button" data-competitor-back>返回竞品列表</button>
      <button type="button" data-competitor-copy="${item.id}">复制链接</button>
      <button type="button" data-competitor-watch="${item.id}">加入观察</button>
    </div>
  </section>
  ${competitorNoticeMarkup()}
  <section class="kpi-grid competitor-detail-metrics">
    <article class="card"><h3>价格</h3><strong class="metric-${competitorStatusClass(item.statusLevel)}">¥${item.price}</strong><span class="card-desc">${item.pricePosition}</span></article>
    <article class="card"><h3>月销</h3><strong>${item.monthlySales}</strong><span class="card-desc">参考销量</span></article>
    <article class="card"><h3>评分</h3><strong>${item.rating}</strong><span class="card-desc">用户反馈</span></article>
    <article class="card"><h3>状态</h3><strong class="metric-${competitorStatusClass(item.statusLevel)}">${item.status}</strong><span class="card-desc">${item.badReview}</span></article>
  </section>
  <section class="page-section competitor-detail-section">
    <div class="section-header"><h3>机会点</h3><span class="status-badge">竞品判断</span></div>
    <p>${item.opportunity}</p>
  </section>
  <section class="page-section competitor-detail-section">
    <div class="section-header"><h3>处理建议</h3><span class="status-badge pending">观察建议</span></div>
    <p>${item.suggestion}</p>
  </section>`;
  bindCompetitorButtons();
}

function bindCompetitorButtons() {
  document.querySelectorAll("[data-competitor-filter-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      openCompetitorFilter = openCompetitorFilter === button.dataset.competitorFilterToggle ? null : button.dataset.competitorFilterToggle;
      renderCompetitorManager();
    });
  });
  document.querySelectorAll("[data-competitor-filter-value]").forEach((button) => {
    button.addEventListener("click", () => {
      const [type, value] = button.dataset.competitorFilterValue.split(":");
      competitorFilters[type] = value;
      openCompetitorFilter = null;
      competitorNotice = "";
      renderCompetitorManager();
    });
  });
  document.querySelector("[data-competitor-search]")?.addEventListener("input", (event) => {
    competitorFilters.search = event.target.value;
    renderCompetitorManager();
    document.querySelector("[data-competitor-search]")?.focus();
  });
  document.querySelectorAll("[data-competitor-detail]").forEach((button) => {
    button.addEventListener("click", () => {
      competitorNotice = "";
      renderCompetitorDetail(button.dataset.competitorDetail);
    });
  });
  document.querySelectorAll("[data-competitor-back]").forEach((button) => {
    button.addEventListener("click", () => {
      activeCompetitorId = null;
      competitorNotice = "";
      renderCompetitorManager();
    });
  });
  document.querySelectorAll("[data-competitor-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const item = competitorManagerPayload.competitors.find((competitor) => competitor.id === button.dataset.competitorCopy);
      if (!item) return;
      try {
        await navigator.clipboard.writeText(item.link);
        competitorNotice = `${item.targetProduct}竞品链接已复制。`;
      } catch {
        competitorNotice = `${item.targetProduct}竞品链接：${item.link}`;
      }
      if (activeCompetitorId) renderCompetitorDetail(activeCompetitorId);
      else renderCompetitorManager();
    });
  });
  document.querySelectorAll("[data-competitor-watch]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = competitorManagerPayload.competitors.find((competitor) => competitor.id === button.dataset.competitorWatch);
      competitorNotice = `${item?.targetProduct || "竞品"}已加入观察清单。`;
      if (activeCompetitorId) renderCompetitorDetail(activeCompetitorId);
      else renderCompetitorManager();
    });
  });
}

function scheduleCompetitorPatch() {
  if (competitorRenderScheduled) return;
  competitorRenderScheduled = true;
  setTimeout(() => {
    competitorRenderScheduled = false;
    if (!isCompetitorRoute()) return;
    if (activeCompetitorId) renderCompetitorDetail(activeCompetitorId);
    else renderCompetitorManager();
  }, 0);
}

const competitorObserver = new MutationObserver(() => {
  if (!isCompetitorRoute()) return;
  if (document.querySelector(".competitor-toolbar") || document.querySelector(".competitor-detail-hero")) return;
  scheduleCompetitorPatch();
});

competitorObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("hashchange", () => {
  activeCompetitorId = null;
  competitorNotice = "";
  openCompetitorFilter = null;
  scheduleCompetitorPatch();
});
window.addEventListener("load", scheduleCompetitorPatch);
scheduleCompetitorPatch();
