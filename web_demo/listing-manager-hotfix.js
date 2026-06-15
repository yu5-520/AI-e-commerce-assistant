const listingManagerPayload = {
  experiments: [
    {
      id: "L001",
      mode: "existing",
      imageLabel: "伞",
      title: "遮阳伞户外便携防晒防紫外线晴雨两用",
      sourceLabel: "已有商品测试",
      platform: "淘宝",
      store: "家居生活主店",
      sourceName: "遮阳伞",
      testType: "主图测试",
      testPlan: "场景图 A / 卖点图 B",
      cycle: "3 天",
      targetMetric: "点击率提升 15%",
      due: "今天 18:00 前确认",
      status: "待确认",
      statusLevel: "warning",
      risk: "库存偏高，先测自然流量，不直接扩大投放。",
      suggestion: "保留原链接，只新增主图测试版本；测试结束后保留点击率更高版本。",
      linkRoute: "business-products",
    },
    {
      id: "L002",
      mode: "existing",
      imageLabel: "架",
      title: "厨房置物架免打孔收纳架壁挂多层家用置物架",
      sourceLabel: "已有商品测试",
      platform: "拼多多",
      store: "家居百货店",
      sourceName: "厨房置物架",
      testType: "标题测试",
      testPlan: "安装场景词 / 收纳容量词",
      cycle: "3 天",
      targetMetric: "搜索点击率提升 10%",
      due: "明天 12:00 前上线",
      status: "测试中",
      statusLevel: "good",
      risk: "不改价格，只测试标题流量入口。",
      suggestion: "标题版本不要同时叠加主图变化，避免无法判断变量来源。",
      linkRoute: "business-products",
    },
    {
      id: "L003",
      mode: "existing",
      imageLabel: "盒",
      title: "透明收纳盒衣柜整理箱家用大容量防尘款",
      sourceLabel: "已有商品测试",
      platform: "淘宝",
      store: "家居生活主店",
      sourceName: "收纳盒",
      testType: "SKU 测试",
      testPlan: "基础款 / 加厚款 / 组合款",
      cycle: "7 天",
      targetMetric: "组合款转化率 ≥ 基础款 80%",
      due: "3 天后复盘",
      status: "待确认",
      statusLevel: "warning",
      risk: "组合款会占用库存，先限制测试库存。",
      suggestion: "先做 2-4 个主推规格，避免一次性铺太多库存。",
      linkRoute: "business-products",
    },
    {
      id: "L004",
      mode: "existing",
      imageLabel: "券",
      title: "平台券活动测试：遮阳伞夏季防晒场景款",
      sourceLabel: "活动测试上新",
      platform: "淘宝",
      store: "家居生活主店",
      sourceName: "遮阳伞",
      testType: "平台券活动",
      testPlan: "店铺券 / 平台券报名版本",
      cycle: "2 天",
      targetMetric: "ROI ≥ 1.3，退款率不升高",
      due: "今天内确认活动价",
      status: "待确认",
      statusLevel: "warning",
      risk: "必须先核算利润安全线和库存承接。",
      suggestion: "活动价不能只看成交量，需同时观察退款率和库存消耗。",
      linkRoute: "business-traffic",
    },
    {
      id: "L005",
      mode: "existing",
      imageLabel: "推",
      title: "搜索推广测试：厨房置物架安装场景词",
      sourceLabel: "推广测试上新",
      platform: "拼多多",
      store: "家居百货店",
      sourceName: "厨房置物架",
      testType: "推广测试",
      testPlan: "搜索词小预算测试",
      cycle: "1 天",
      targetMetric: "点击成本可控，收藏加购率达标",
      due: "今天 20:00 前观察首轮数据",
      status: "测试中",
      statusLevel: "good",
      risk: "不直接放大预算，先看词包质量。",
      suggestion: "先测安装、收纳、免打孔三组词，避免一次性混投。",
      linkRoute: "business-traffic",
    },
    {
      id: "L006",
      mode: "competitor",
      imageLabel: "装",
      title: "厨房置物架：新增安装说明图 + 尺寸参照图版本",
      sourceLabel: "竞品机会测试",
      platform: "拼多多",
      store: "家居百货店",
      sourceName: "竞品差评：安装困难 / 尺寸不符",
      testType: "详情页测试",
      testPlan: "安装图 + 尺寸图 + 承重说明",
      cycle: "5 天",
      targetMetric: "退款原因中尺寸/安装问题下降",
      due: "明天 18:00 前出测试版本",
      status: "待确认",
      statusLevel: "warning",
      risk: "不建议直接跟低价，先补承接说明。",
      suggestion: "从竞品差评反推详情页补强点，先小范围测试。",
      linkRoute: "business-competitors",
    },
    {
      id: "L007",
      mode: "competitor",
      imageLabel: "骨",
      title: "遮阳伞：强化伞骨稳定和收纳体验主图版本",
      sourceLabel: "竞品机会测试",
      platform: "淘宝",
      store: "家居生活主店",
      sourceName: "竞品差评：伞骨不稳 / 收纳袋小",
      testType: "主图测试",
      testPlan: "结构稳定图 / 收纳对比图",
      cycle: "3 天",
      targetMetric: "点击率提升 12%，咨询中结构问题下降",
      due: "2 天后复盘",
      status: "待确认",
      statusLevel: "warning",
      risk: "不能夸大防晒、防风和耐用承诺。",
      suggestion: "主图强调真实结构，不使用无依据极限词。",
      linkRoute: "business-competitors",
    },
    {
      id: "L008",
      mode: "competitor",
      imageLabel: "垫",
      title: "护腰坐垫：材质说明和支撑实测版本",
      sourceLabel: "竞品机会测试",
      platform: "抖音小店",
      store: "家居好物号",
      sourceName: "竞品差评：支撑不足 / 材质偏软",
      testType: "卖点测试",
      testPlan: "材质实拍 + 支撑对比 + 使用场景",
      cycle: "5 天",
      targetMetric: "售后敏感咨询下降，转化率不低于基准版",
      due: "本周内上线测试",
      status: "待观察",
      statusLevel: "danger",
      risk: "售后归因完成前不建议放量。",
      suggestion: "先做内容承接测试，不直接报名大促或加大推广。",
      linkRoute: "business-competitors",
    },
  ],
};

let activeListingMode = "existing";
let activeListingId = null;
let listingNotice = "";
let listingRenderScheduled = false;
const listingDecisionState = {};

function isListingRoute() {
  return location.hash.replace("#", "") === "business-listing" || document.querySelector('.nav a[data-route="business-listing"]')?.classList.contains("active");
}

function listingStatusClass(level) {
  return level === "danger" ? "danger" : level === "warning" ? "warning" : "good";
}

function listingNoticeMarkup() {
  if (!listingNotice) return "";
  return `<section class="listing-notice"><strong>操作结果</strong><span>${listingNotice}</span></section>`;
}

function listingExperiments() {
  return listingManagerPayload.experiments.filter((item) => item.mode === activeListingMode);
}

function listingMetrics() {
  const items = listingManagerPayload.experiments;
  return [
    { label: "待确认测试", value: items.filter((item) => (listingDecisionState[item.id] || item.status) === "待确认").length, desc: "需要人工确认" },
    { label: "进行中测试", value: items.filter((item) => (listingDecisionState[item.id] || item.status) === "测试中").length, desc: "正在观察数据" },
    { label: "今日到期", value: 2, desc: "需要复盘处理" },
    { label: "竞品触发", value: items.filter((item) => item.mode === "competitor").length, desc: "来自竞品机会" },
  ];
}

function renderListingTabs() {
  return `<div class="listing-tabs">
    <button type="button" class="${activeListingMode === "existing" ? "active" : ""}" data-listing-tab="existing">已有商品测试</button>
    <button type="button" class="${activeListingMode === "competitor" ? "active" : ""}" data-listing-tab="competitor">竞品机会测试</button>
  </div>`;
}

function renderListingCard(item) {
  const status = listingDecisionState[item.id] || item.status;
  const level = status === "已确认" ? "good" : item.statusLevel;
  return `<article class="listing-card">
    <div class="listing-title-cell">
      <div class="listing-thumb">${item.imageLabel}</div>
      <div>
        <strong>${item.title}</strong>
        <small>${item.id} · ${item.platform} · ${item.store}</small>
        <span>来源：${item.sourceLabel} · ${item.sourceName}</span>
      </div>
    </div>
    <div class="listing-metric-strip">
      <div class="listing-number-cell"><span>测试类型</span><strong>${item.testType}</strong><small>${item.testPlan}</small></div>
      <div class="listing-number-cell"><span>测试周期</span><strong>${item.cycle}</strong><small>${item.due}</small></div>
      <div class="listing-number-cell"><span>目标指标</span><strong>${item.targetMetric}</strong><small>到期复盘</small></div>
      <div class="listing-number-cell ${listingStatusClass(level)}"><span>状态</span><strong>${status}</strong><small>${item.risk}</small></div>
    </div>
    <div class="listing-actions">
      <button type="button" data-listing-detail="${item.id}">详情</button>
      <button type="button" data-listing-confirm="${item.id}">确认测试</button>
      <button type="button" data-listing-task="${item.id}">加入任务清单</button>
    </div>
  </article>`;
}

function renderListingManager() {
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!appView || !title || !isListingRoute()) return;
  const items = listingExperiments();
  activeListingId = null;
  title.textContent = "上新";
  appView.innerHTML = `<section class="listing-toolbar">
    <div>
      <p class="eyebrow">LAUNCH TEST</p>
      <h2>上新测试台</h2>
      <p>管理已有商品测试上新和竞品机会测试上新；先创建测试版本，再确认、观察、复盘。</p>
    </div>
    ${renderListingTabs()}
  </section>
  ${listingNoticeMarkup()}
  <section class="kpi-grid listing-metrics">
    ${listingMetrics().map((item) => `<article class="card listing-metric-card"><h3>${item.label}</h3><strong>${item.value}</strong><span class="card-desc">${item.desc}</span></article>`).join("")}
  </section>
  <section class="page-section listing-list-section">
    <div class="section-header">
      <h3>${activeListingMode === "existing" ? "已有商品测试" : "竞品机会测试"}</h3>
      <span class="status-badge">${items.length} 个测试</span>
    </div>
    <div class="listing-card-list">
      ${items.map(renderListingCard).join("")}
    </div>
  </section>`;
  bindListingButtons();
}

function renderListingDetail(listingId) {
  const item = listingManagerPayload.experiments.find((experiment) => experiment.id === listingId);
  const appView = document.getElementById("appView");
  const title = document.getElementById("pageTitle");
  if (!item || !appView || !title) return;
  activeListingId = listingId;
  title.textContent = "上新测试";
  const status = listingDecisionState[item.id] || item.status;
  appView.innerHTML = `<section class="listing-detail-hero">
    <div class="listing-detail-main">
      <div class="listing-thumb large">${item.imageLabel}</div>
      <div>
        <p class="eyebrow">LAUNCH TEST DETAIL</p>
        <h2>${item.title}</h2>
        <p>${item.platform} · ${item.store} · ${item.sourceLabel}</p>
        <span>${item.sourceName}</span>
      </div>
    </div>
    <div class="listing-detail-actions">
      <button type="button" data-listing-back>返回上新测试台</button>
      <button type="button" data-listing-confirm="${item.id}">确认测试</button>
      <button type="button" data-listing-task="${item.id}">加入任务清单</button>
      <button type="button" data-listing-source="${item.linkRoute}">查看来源</button>
    </div>
  </section>
  ${listingNoticeMarkup()}
  <section class="kpi-grid listing-detail-metrics">
    <article class="card"><h3>测试类型</h3><strong>${item.testType}</strong><span class="card-desc">${item.testPlan}</span></article>
    <article class="card"><h3>测试周期</h3><strong>${item.cycle}</strong><span class="card-desc">${item.due}</span></article>
    <article class="card"><h3>目标指标</h3><strong>${item.targetMetric}</strong><span class="card-desc">到期复盘</span></article>
    <article class="card"><h3>状态</h3><strong class="metric-${listingStatusClass(item.statusLevel)}">${status}</strong><span class="card-desc">人工确认后执行</span></article>
  </section>
  <section class="page-section listing-detail-section">
    <div class="section-header"><h3>风险提示</h3><span class="status-badge pending">执行边界</span></div>
    <p>${item.risk}</p>
  </section>
  <section class="page-section listing-detail-section">
    <div class="section-header"><h3>测试建议</h3><span class="status-badge">上新动作</span></div>
    <p>${item.suggestion}</p>
  </section>`;
  bindListingButtons();
}

function bindListingButtons() {
  document.querySelectorAll("[data-listing-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      activeListingMode = button.dataset.listingTab;
      listingNotice = "";
      renderListingManager();
    });
  });
  document.querySelectorAll("[data-listing-detail]").forEach((button) => {
    button.addEventListener("click", () => {
      listingNotice = "";
      renderListingDetail(button.dataset.listingDetail);
    });
  });
  document.querySelectorAll("[data-listing-back]").forEach((button) => {
    button.addEventListener("click", () => {
      activeListingId = null;
      listingNotice = "";
      renderListingManager();
    });
  });
  document.querySelectorAll("[data-listing-confirm]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = listingManagerPayload.experiments.find((experiment) => experiment.id === button.dataset.listingConfirm);
      if (!item) return;
      listingDecisionState[item.id] = "已确认";
      listingNotice = `${item.testType}已确认，下一步进入确认页人工执行。`;
      if (activeListingId) renderListingDetail(activeListingId);
      else renderListingManager();
    });
  });
  document.querySelectorAll("[data-listing-task]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = listingManagerPayload.experiments.find((experiment) => experiment.id === button.dataset.listingTask);
      listingNotice = `${item?.testType || "上新测试"}已加入任务清单。`;
      if (activeListingId) renderListingDetail(activeListingId);
      else renderListingManager();
    });
  });
  document.querySelectorAll("[data-listing-source]").forEach((button) => {
    button.addEventListener("click", () => {
      location.hash = button.dataset.listingSource;
    });
  });
}

function scheduleListingPatch() {
  if (listingRenderScheduled) return;
  listingRenderScheduled = true;
  setTimeout(() => {
    listingRenderScheduled = false;
    if (!isListingRoute()) return;
    if (activeListingId) renderListingDetail(activeListingId);
    else renderListingManager();
  }, 0);
}

const listingObserver = new MutationObserver(() => {
  if (!isListingRoute()) return;
  if (document.querySelector(".listing-toolbar") || document.querySelector(".listing-detail-hero")) return;
  scheduleListingPatch();
});

listingObserver.observe(document.body, { childList: true, subtree: true });
window.addEventListener("hashchange", () => {
  activeListingId = null;
  listingNotice = "";
  scheduleListingPatch();
});
window.addEventListener("load", scheduleListingPatch);
scheduleListingPatch();
