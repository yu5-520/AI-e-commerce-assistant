const trafficManagerPayload = {
  tests: [
    {
      id: "T001",
      productId: "P001",
      imageLabel: "伞",
      title: "遮阳伞户外便携防晒防紫外线晴雨两用",
      platform: "淘宝",
      store: "家居生活主店",
      link: "https://shop.example.com/products/P001",
      channel: "自然搜索",
      source: "主图测试回流",
      target: "点击率提升 15%",
      cycle: "3 天",
      exposure: "4,800",
      ctr: "5.2%",
      conversion: "2.4%",
      roi: "1.6",
      refundRate: "2.1%",
      inventory: 200,
      status: "可小幅放量",
      statusLevel: "good",
      backflow: "经营判断",
      nextStep: "保留点击率更高主图，小幅提高自然流量承接。",
    },
    {
      id: "T002",
      productId: "P002",
      imageLabel: "架",
      title: "厨房置物架免打孔收纳架壁挂多层家用置物架",
      platform: "拼多多",
      store: "家居百货店",
      link: "https://shop.example.com/products/P002",
      channel: "搜索推广",
      source: "推广测试回流",
      target: "安装场景词小预算测试",
      cycle: "1 天",
      exposure: "2,100",
      ctr: "3.9%",
      conversion: "1.7%",
      roi: "1.1",
      refundRate: "6.8%",
      inventory: 120,
      status: "先查售后",
      statusLevel: "danger",
      backflow: "售后归因",
      nextStep: "先查尺寸、安装、物流和客服承诺，不继续放大预算。",
    },
    {
      id: "T003",
      productId: "P003",
      imageLabel: "垫",
      title: "护腰坐垫久坐办公室靠垫人体工学支撑款",
      platform: "抖音小店",
      store: "家居好物号",
      link: "https://shop.example.com/products/P003",
      channel: "推荐流量",
      source: "竞品机会测试回流",
      target: "支撑实测内容承接",
      cycle: "5 天",
      exposure: "6,300",
      ctr: "4.1%",
      conversion: "1.2%",
      roi: "0.9",
      refundRate: "8.4%",
      inventory: 80,
      status: "暂停投放",
      statusLevel: "danger",
      backflow: "商品复查",
      nextStep: "售后敏感未解决前暂停放量，回到材质和支撑说明测试。",
    },
    {
      id: "T004",
      productId: "P004",
      imageLabel: "盒",
      title: "透明收纳盒衣柜整理箱家用大容量防尘款",
      platform: "淘宝",
      store: "家居生活主店",
      link: "https://shop.example.com/products/P004",
      channel: "活动流量",
      source: "平台券活动测试",
      target: "ROI ≥ 1.3，退款率不升高",
      cycle: "2 天",
      exposure: "3,900",
      ctr: "4.7%",
      conversion: "2.2%",
      roi: "1.3",
      refundRate: "3.4%",
      inventory: 46,
      status: "谨慎放量",
      statusLevel: "warning",
      backflow: "库存承接",
      nextStep: "库存接近安全线，先确认补货周期，再决定是否继续活动。",
    },
    {
      id: "T005",
      productId: "P002",
      imageLabel: "架",
      title: "厨房置物架免打孔收纳架壁挂多层家用置物架",
      platform: "拼多多",
      store: "家居百货店",
      link: "https://shop.example.com/products/P002",
      channel: "自然搜索",
      source: "标题测试回流",
      target: "搜索点击率提升 10%",
      cycle: "3 天",
      exposure: "5,600",
      ctr: "4.9%",
      conversion: "2.0%",
      roi: "1.4",
      refundRate: "5.9%",
      inventory: 120,
      status: "继续观察",
      statusLevel: "warning",
      backflow: "售后归因",
      nextStep: "标题带来点击提升，但退款率仍偏高，先观察安装相关咨询。",
    },
    {
      id: "T006",
      productId: "P001",
      imageLabel: "伞",
      title: "遮阳伞户外便携防晒防紫外线晴雨两用",
      platform: "淘宝",
      store: "家居生活主店",
      link: "https://shop.example.com/products/P001",
      channel: "平台券",
      source: "活动报名测试",
      target: "活动 ROI ≥ 1.5",
      cycle: "2 天",
      exposure: "7,200",
      ctr: "5.6%",
      conversion: "2.8%",
      roi: "1.7",
      refundRate: "2.5%",
      inventory: 200,
      status: "可小幅放量",
      statusLevel: "good",
      backflow: "经营判断",
      nextStep: "活动表现稳定，可小幅增加库存承接和活动曝光。",
    },
  ],
};

let activeTrafficId = null;
let trafficNotice = "";
let openTrafficFilter = null;
let trafficRenderScheduled = false;
const trafficFilters = {
  platform: "全部平台",
  store: "全部店铺",
  channel: "全部入口",
  status: "全部状态",
  search: "",
};

function isTrafficRoute() {
  return location.hash.replace("#", "") === "business-traffic" || document.querySelector('.nav a[data-route="business-traffic"]')?.classList.contains("active");
}

function trafficStatusClass(level) {
  return level === "danger" ? "danger" : level === "warning" ? "warning" : "good";
}

function trafficNoticeMarkup() {
  if (!trafficNotice) return "";
  return `<section class="traffic-notice"><strong>操作结果</strong><span>${trafficNotice}</span></section>`;
}

function trafficFilterOptions(type) {
  if (type === "platform") return ["全部平台", ...new Set(trafficManagerPayload.tests.map((item) => item.platform))];
  if (type === "store") return ["全部店铺", ...new Set(trafficManagerPayload.tests.map((item) => item.store))];
  if (type === "channel") return ["全部入口", ...new Set(trafficManagerPayload.tests.map((item) => item.channel))];
  return ["全部状态", "可小幅放量", "谨慎放量", "继续观察", "先查售后", "暂停投放"];
}

function renderTrafficFilter(type, label) {
  const value = trafficFilters[type];
  const isOpen = openTrafficFilter === type;
  return `<div class="traffic-filter-menu ${isOpen ? "open" : ""}">
    <button type="button" data-traffic-filter-toggle="${type}">${label}：${value} <span>⌄</span></button>
    <div class="traffic-filter-options">
      ${trafficFilterOptions(type).map((option) => `<button type="button" class="${option === value ? "selected" : ""}" data-traffic-filter-value="${type}:${option}">${option}</button>`).join("")}
    </div>
  </div>`;
}

function trafficMatchesFilters(item) {
  if (trafficFilters.platform !== "全部平台" && item.platform !== trafficFilters.platform) return false;
  if (trafficFilters.store !== "全部店铺" && item.store !== trafficFilters.store) return false;
  if (trafficFilters.channel !== "全部入口" && item.channel !== trafficFilters.channel) return false;
  if (trafficFilters.status !== "全部状态" && item.status !== trafficFilters.status) return false;
  const keyword = trafficFilters.search.trim().toLowerCase();
  if (!keyword) return true;
  return [item.id, item.productId, item.title, item.platform, item.store, item.channel, item.source, item.status, item.backflow, item.nextStep]
    .join(" ")
    .toLowerCase()
    .includes(keyword);
}

function filteredTrafficTests() {
  return trafficManagerPayload.tests.filter(trafficMatchesFilters);
}

function trafficMetrics() {
  const items = trafficManagerPayload.tests;
  return [
    { label: "测试中", value: items.length, desc: "商品级流量测试" },
    { label: "待确认", value: items.filter((item) => item.statusLevel !== "good").length, desc: "需要人工判断" },
    { label: "今日到期", value: 2, desc: "需要复盘" },
    { label: "可放量", value: items.filter((item) => item.status === "可小幅放量").length, desc: "先小幅验证" },
  ];
}

function trafficFilterSummary(count) {
  const active = [
    trafficFilters.platform !== "全部平台" ? trafficFilters.platform : null,
    trafficFilters.store !== "全部店铺" ? trafficFilters.store : null,
    trafficFilters.channel !== "全部入口" ? trafficFilters.channel : null,
    trafficFilters.status !== "全部状态" ? trafficFilters.status : null,
    trafficFilters.search.trim() ? `搜索：${trafficFilters.search.trim()}` : null,
  ].filter(Boolean);
  return active.length ? `${count} 条测试 · ${active.join(" / ")}` : `${count} 条测试`;
}

function renderTrafficRow(item) {
  return `<article class="traffic-row">
    <div class="traffic-title-cell">
      <div class="traffic-thumb">${item.imageLabel}</div>
      <div class="traffic-title-block">
        <strong>${item.title}</strong>
        <small>${item.productId} · <a href="${item.link}" target="_blank" rel="noreferrer">查看商品链接</a></small>
        <span>${item.platform} · ${item.store} · ${item.source}</span>
      </div>
    </div>
    <div class="traffic-metric-strip">
      <div class="traffic-number-cell"><span>入口</span><strong>${item.channel}</strong><small>${item.target}</small></div>
      <div class="traffic-number-cell"><span>曝光 / 点击率</span><strong>${item.exposure}</strong><small>CTR ${item.ctr}</small></div>
      <div class="traffic-number-cell"><span>转化 / ROI</span><strong>${item.conversion}</strong><small>ROI ${item.roi}</small></div>
      <div class="traffic-number-cell ${trafficStatusClass(item.statusLevel)}"><span>状态</span><strong>${item.status}</strong><small>${item.backflow}</small></div>
    </div>
    <div class="traffic-backflow">
      <span>下一步</span>
      <strong>${item.nextStep}</strong>
    </div>
    <div class="traffic-actions">
      <button type="button" data-traffic-detail="${item.id}">详情</button>
      <button type="button" data-traffic-watch="${item.id}">继续观察</button>
      <button type="button" data-traffic-task="${item.id}">加入任务清单</button>
    </div>
  </article>`;
}

function renderTrafficManager() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || !isTrafficRoute()) return;
  const tests = filteredTrafficTests();
  activeTrafficId = null;
  title.textContent = "流量";
  appView.innerHTML = `<section class="traffic-toolbar">
    <div>
      <p class="eyebrow">TRAFFIC TEST</p>
      <h2>流量测试台</h2>
      <p>每条流量判断都绑定具体商品、平台、店铺和链接，观察曝光、点击、转化、ROI、退款率和库存承接。</p>
    </div>
    <div class="traffic-filter-row">
      ${renderTrafficFilter("platform", "平台")}
      ${renderTrafficFilter("store", "店铺")}
      ${renderTrafficFilter("channel", "入口")}
      ${renderTrafficFilter("status", "状态")}
      <label class="traffic-search"><input type="search" value="${trafficFilters.search}" placeholder="搜索商品 / 入口" data-traffic-search /></label>
    </div>
  </section>
  ${trafficNoticeMarkup()}
  <section class="kpi-grid traffic-metrics">
    ${trafficMetrics().map((item) => `<article class="card traffic-metric-card"><h3>${item.label}</h3><strong>${item.value}</strong><span class="card-desc">${item.desc}</span></article>`).join("")}
  </section>
  <section class="page-section traffic-list-section">
    <div class="section-header">
      <h3>商品级流量测试</h3>
      <span class="status-badge">${trafficFilterSummary(tests.length)}</span>
    </div>
    <div class="traffic-card-list">
      ${tests.length ? tests.map(renderTrafficRow).join("") : `<div class="traffic-empty">当前筛选条件下没有流量测试。</div>`}
    </div>
  </section>`;
  bindTrafficButtons();
}

function renderTrafficDetail(trafficId) {
  const item = trafficManagerPayload.tests.find((test) => test.id === trafficId);
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!item || !appView || !title) return;
  activeTrafficId = trafficId;
  openTrafficFilter = null;
  title.textContent = "流量测试";
  appView.innerHTML = `<section class="traffic-detail-hero">
    <div class="traffic-detail-main">
      <div class="traffic-thumb large">${item.imageLabel}</div>
      <div>
        <p class="eyebrow">TRAFFIC TEST DETAIL</p>
        <h2>${item.title}</h2>
        <p>${item.platform} · ${item.store} · ${item.channel}</p>
        <a href="${item.link}" target="_blank" rel="noreferrer">${item.link}</a>
      </div>
    </div>
    <div class="traffic-detail-actions">
      <button type="button" data-traffic-back>返回流量测试台</button>
      <button type="button" data-traffic-source="business-products">查看商品</button>
      <button type="button" data-traffic-source="business-listing">查看上新</button>
      <button type="button" data-traffic-task="${item.id}">加入任务清单</button>
    </div>
  </section>
  ${trafficNoticeMarkup()}
  <section class="kpi-grid traffic-detail-metrics">
    <article class="card"><h3>曝光</h3><strong>${item.exposure}</strong><span class="card-desc">CTR ${item.ctr}</span></article>
    <article class="card"><h3>转化率</h3><strong>${item.conversion}</strong><span class="card-desc">ROI ${item.roi}</span></article>
    <article class="card"><h3>退款率</h3><strong class="metric-${trafficStatusClass(item.statusLevel)}">${item.refundRate}</strong><span class="card-desc">库存 ${item.inventory}</span></article>
    <article class="card"><h3>状态</h3><strong class="metric-${trafficStatusClass(item.statusLevel)}">${item.status}</strong><span class="card-desc">${item.backflow}</span></article>
  </section>
  <section class="page-section traffic-detail-section">
    <div class="section-header"><h3>测试目标</h3><span class="status-badge">${item.cycle}</span></div>
    <p>${item.target}</p>
  </section>
  <section class="page-section traffic-detail-section">
    <div class="section-header"><h3>下一步</h3><span class="status-badge pending">${item.backflow}</span></div>
    <p>${item.nextStep}</p>
  </section>`;
  bindTrafficButtons();
}

function bindTrafficButtons() {
  document.querySelectorAll("[data-traffic-filter-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      openTrafficFilter = openTrafficFilter === button.dataset.trafficFilterToggle ? null : button.dataset.trafficFilterToggle;
      renderTrafficManager();
    });
  });
  document.querySelectorAll("[data-traffic-filter-value]").forEach((button) => {
    button.addEventListener("click", () => {
      const [type, value] = button.dataset.trafficFilterValue.split(":");
      trafficFilters[type] = value;
      openTrafficFilter = null;
      trafficNotice = "";
      renderTrafficManager();
    });
  });
  document.querySelector("[data-traffic-search]")?.addEventListener("input", (event) => {
    trafficFilters.search = event.target.value;
    renderTrafficManager();
    document.querySelector("[data-traffic-search]")?.focus();
  });
  document.querySelectorAll("[data-traffic-detail]").forEach((button) => {
    button.addEventListener("click", () => {
      trafficNotice = "";
      renderTrafficDetail(button.dataset.trafficDetail);
    });
  });
  document.querySelectorAll("[data-traffic-back]").forEach((button) => {
    button.addEventListener("click", () => {
      activeTrafficId = null;
      trafficNotice = "";
      renderTrafficManager();
    });
  });
  document.querySelectorAll("[data-traffic-watch]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = trafficManagerPayload.tests.find((test) => test.id === button.dataset.trafficWatch);
      trafficNotice = `${item?.title || "商品"}已标记继续观察。`;
      if (activeTrafficId) renderTrafficDetail(activeTrafficId);
      else renderTrafficManager();
    });
  });
  document.querySelectorAll("[data-traffic-task]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = trafficManagerPayload.tests.find((test) => test.id === button.dataset.trafficTask);
      trafficNotice = `${item?.channel || "流量测试"}已加入任务清单。`;
      if (activeTrafficId) renderTrafficDetail(activeTrafficId);
      else renderTrafficManager();
    });
  });
  document.querySelectorAll("[data-traffic-source]").forEach((button) => {
    button.addEventListener("click", () => {
      location.hash = button.dataset.trafficSource;
    });
  });
}

function scheduleTrafficPatch() {
  if (trafficRenderScheduled) return;
  trafficRenderScheduled = true;
  setTimeout(() => {
    trafficRenderScheduled = false;
    if (!isTrafficRoute()) return;
    if (activeTrafficId) renderTrafficDetail(activeTrafficId);
    else renderTrafficManager();
  }, 0);
}

const trafficObserver = new MutationObserver(() => {
  if (!isTrafficRoute()) return;
  if (document.querySelector(".traffic-toolbar") || document.querySelector(".traffic-detail-hero")) return;
  scheduleTrafficPatch();
});

trafficObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("hashchange", () => {
  activeTrafficId = null;
  trafficNotice = "";
  openTrafficFilter = null;
  scheduleTrafficPatch();
});
window.addEventListener("load", scheduleTrafficPatch);
scheduleTrafficPatch();
