const fallbackData = {
  summary: {
    unit_name: "家居生活商品",
    operating_unit_id: "home_living_goods",
    cycle_frequency: "daily",
    product_count: 3,
    customer_count: 4,
    competitor_count: 4,
    listing_candidate_count: 4,
    traffic_experiment_count: 4,
    approval_required_count: 13,
    loop_next_module: "crm_after_sales_diagnosis",
  },
  operating_unit: {
    unit_name: "家居生活商品",
    operating_unit_id: "home_living_goods",
    dominant_product_group: "home_living_goods",
    product_group_summary: { sun_protection_goods: 1, home_storage_goods: 1, health_home_goods: 1 },
    reason: "根据 Mock ERP 商品结构识别",
  },
  cycle_policy: {
    cycle_frequency: "daily",
    run_time: "09:00",
    report_type: "daily_operation_report",
    trigger_rules: ["库存异常", "退款异常", "ROI 低", "点击异常", "转化异常"],
  },
  product_diagnosis: [
    { product_id: "P001", product_name: "遮阳伞", risk_level: "medium", risks: ["库存高", "活动价风险"], suggested_actions: ["复核活动价", "观察主图点击"], gross_margin: 8.2, activity_margin: 1.2, stock: 200 },
    { product_id: "P002", product_name: "厨房置物架", risk_level: "medium", risks: ["库存偏高"], suggested_actions: ["补安装说明", "检查尺寸承重"], gross_margin: 12.4, activity_margin: 6.4, stock: 120 },
    { product_id: "P003", product_name: "护腰坐垫", risk_level: "high", risks: ["退款异常"], suggested_actions: ["售后归因", "优化材质尺寸说明"], gross_margin: 11.5, activity_margin: 5.5, stock: 80 },
  ],
  competitor_analysis: {
    competitor_count: 4,
    reference_product: { product_name: "护腰坐垫", trigger_reason: "退款异常" },
    price_gap: { position: "within_market", insight: "价格可测" },
    review_gap: { top_bad_review_keywords: ["尺寸不符", "材质偏软", "支撑不明显"], opportunity_actions: ["补尺寸参照", "明确材质", "优化售后说明"] },
    next_action: "优化尺寸与客服承接",
  },
  listing_growth_plan: {
    candidate_count: 4,
    top_candidate: { supplier_product_id: "SHL002", product_name: "免打孔厨房置物架", score: 89, expected_margin: 35, margin_rate: 0.5932, reasons: ["匹配经营单元", "库存承接好"], risks: ["安装咨询"] },
    listing_draft: { title_draft: "免打孔厨房置物架 收纳 节省空间 家用多场景款", image_plan: ["场景图", "尺寸图", "安装图"], sku_plan: ["2-4 个主规格", "区分基础 / 升级款"], compliance_checklist: ["复核承重", "复核成本", "人工确认"] },
    next_action: "复核后小流量测试",
  },
  traffic_feedback_report: {
    experiment_count: 4,
    next_action: "先查售后",
    loopback_actions: ["售后归因", "预算止损"],
    diagnoses: [
      { experiment_id: "THL001", product_id: "P001", traffic_source: "自然搜索", roi: 1.7, decision: "continue_testing", risk_level: "low", recommended_actions: ["继续观察"] },
      { experiment_id: "THL003", product_id: "P003", traffic_source: "付费测试", roi: 0.72, decision: "enter_after_sales_diagnosis", risk_level: "high", recommended_actions: ["售后归因"] },
    ],
  },
  operating_loop_summary: {
    next_module: "crm_after_sales_diagnosis",
    next_iteration_plan: ["售后归因", "复核尺寸材质", "暂停放量"],
  },
  rpa_tasks: [
    { task_id: "TASK_PRODUCT_DAILY_001", task_type: "经营日报", risk_level: "low", ai_suggestion: "生成经营日报" },
    { task_id: "TASK_SKU_PRICE_001", task_type: "价格复核", risk_level: "medium", ai_suggestion: "复核价格与保本线" },
    { task_id: "TASK_CRM_AFTER_SALES_004", task_type: "售后归因", risk_level: "high", ai_suggestion: "检查尺寸、材质、物流" },
  ],
};
fallbackData.approval_required_tasks = fallbackData.rpa_tasks;

const state = {
  rawWorkflow: fallbackData,
  businessToday: null,
  apiMode: false,
  importValidation: null,
  reportText: "",
  productsView: null,
  competitorsView: null,
  listingView: null,
  trafficView: null,
  actionsView: null,
};

const routes = {
  dashboard: ["总览", renderDashboard],
  "operating-unit": ["经营单元", renderOperatingUnit],
  "data-check": ["数据", renderDataCheck],
  "business-products": ["商品", renderProducts],
  "business-competitors": ["竞品", renderCompetitors],
  "business-listing": ["上新", renderListing],
  "business-traffic": ["流量", renderTraffic],
  "business-actions": ["确认", renderApprovals],
  "business-report": ["报告", renderReports],
};

const legacyRouteMap = {
  products: "business-products",
  competitors: "business-competitors",
  listing: "business-listing",
  traffic: "business-traffic",
  approvals: "business-actions",
  reports: "business-report",
};

const $ = (id) => document.getElementById(id);
const view = () => $("appView");
const raw = () => state.rawWorkflow || fallbackData;
const safeArray = (value) => Array.isArray(value) ? value : [];
const cnFrequency = (frequency) => ({ daily: "每日", weekly: "每周", monthly: "每月" }[frequency] || frequency || "未设定");
const cnDecision = (decision) => ({
  enter_after_sales_diagnosis: "售后",
  stop_or_reduce_budget: "止损",
  change_title_or_main_image: "换图",
  adjust_sku_price_or_detail_page: "调价",
  scale_carefully: "放量",
  continue_testing: "观察",
}[decision] || decision || "观察");
const cnModule = (module) => ({
  crm_after_sales_diagnosis: "售后归因",
  erp_profit_and_budget_review: "利润复核",
  competitor_title_image_review: "主图复查",
  listing_sku_pricing_review: "规格定价",
  erp_product_risk_review: "商品风险",
  controlled_scale_review: "谨慎放量",
  continue_operating_loop: "继续循环",
}[module] || module || "继续循环");

const riskLabel = (level) => ({ high: "高", medium: "中", low: "低" }[level] || "低");
const urgencyLabel = (level) => ({ high: "紧急", medium: "中", low: "观察" }[level] || "观察");
const badge = (level) => `<span class="badge ${level || "low"}">${riskLabel(level)}</span>`;
const urgencyBadge = (level, label) => `<span class="badge ${level || "low"}">${label || urgencyLabel(level)}</span>`;
const statusBadge = (status) => `<span class="status-badge ${status || "ready"}">${({ passed: "通过", success: "完成", failed: "失败", running: "运行", approved: "确认", rejected: "拒绝", pending: "待定", preview: "演示", ready: "可用" }[status]) || status || "可用"}</span>`;
const card = (title, body, extra = "") => `<article class="card ${extra}"><h3>${title}</h3>${body}</article>`;
const list = (items) => `<ul class="clean-list">${safeArray(items).map((item) => `<li>${item}</li>`).join("")}</ul>`;
const kv = (items) => `<div class="info-list">${items.map(([key, value]) => `<div><span>${key}</span><strong>${value ?? "-"}</strong></div>`).join("")}</div>`;

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

async function fetchProductView(url, fallbackValue) {
  if (!state.apiMode) return fallbackValue;
  try {
    return await fetchJson(url);
  } catch {
    return fallbackValue;
  }
}

async function refreshWorkflow() {
  try {
    const payload = await fetchJson("/api/business/today");
    state.businessToday = payload;
    state.rawWorkflow = payload.raw || fallbackData;
    state.apiMode = true;
    state.reportText = "";
    state.productsView = null;
    state.competitorsView = null;
    state.listingView = null;
    state.trafficView = null;
    state.actionsView = null;
    $("apiModeBadge").textContent = "在线";
    $("apiModeBadge").className = "mode-badge api";
  } catch {
    state.businessToday = null;
    state.rawWorkflow = fallbackData;
    state.apiMode = false;
    $("apiModeBadge").textContent = "演示";
    $("apiModeBadge").className = "mode-badge local";
  }
}

async function renderRoute() {
  const hash = location.hash.replace("#", "");
  const route = routes[hash] ? hash : (legacyRouteMap[hash] || "dashboard");
  document.querySelectorAll(".nav a").forEach((link) => link.classList.toggle("active", link.dataset.route === route));
  const [title, renderer] = routes[route];
  $("pageTitle").textContent = title;
  await renderer();
}

function fallbackTaskQueue(d) {
  const s = d.summary || {};
  const loop = d.operating_loop_summary || {};
  const traffic = d.traffic_feedback_report || {};
  return [
    {
      rank: 1,
      title: "复查高退款商品",
      urgency: "紧急",
      urgency_level: "high",
      deadline: "今天 18:00 前",
      count: Math.max(1, safeArray(d.product_diagnosis).filter((item) => item.risk_level === "high").length || 3),
      impact: "退款率 / 评分",
      reason: "退款异常商品需要先复查尺码、材质、物流和客服承诺。",
    },
    {
      rank: 2,
      title: "确认售后敏感问题",
      urgency: "紧急",
      urgency_level: "high",
      deadline: "今天内",
      count: 1,
      impact: "客服承接",
      reason: "售后问题未归因前，不建议继续放量。",
    },
    {
      rank: 3,
      title: "小范围流量测试",
      urgency: "中",
      urgency_level: "medium",
      deadline: "明天 12:00 前",
      count: s.traffic_experiment_count || traffic.experiment_count || 0,
      impact: "ROI / 库存承接",
      reason: "可继续小幅测试，但必须观察退款率、ROI 和库存承接。",
    },
    {
      rank: 4,
      title: "上新前确认素材",
      urgency: "中",
      urgency_level: "medium",
      deadline: "明天内",
      count: s.listing_candidate_count || 0,
      impact: "转化率",
      reason: safeArray(loop.next_iteration_plan).join(" / ") || "确认后再进入下一步。",
    },
  ];
}

function renderTaskQueue(tasks) {
  const rows = safeArray(tasks).map((task, index) => `<article class="dashboard-task-card">
    <div class="task-rank">${task.rank || index + 1}</div>
    <div class="task-main">
      <h3>${task.title || task.task_type || "待处理任务"}</h3>
      <div class="task-meta">
        ${urgencyBadge(task.urgency_level || task.risk_level, task.urgency)}
        <span>${task.deadline || "待定"}</span>
        <span>${task.count ?? 1} 项</span>
        <span>${task.impact || "经营承接"}</span>
      </div>
      <p>${task.reason || task.ai_suggestion || task.suggestion || "确认后再进入下一步。"}</p>
    </div>
  </article>`).join("");
  return `<section class="dashboard-task-list">${rows}</section>`;
}

function renderDashboard() {
  const d = raw();
  const today = state.businessToday;
  const s = d.summary || {};
  const loop = d.operating_loop_summary || {};
  const traffic = d.traffic_feedback_report || {};
  const priority = today?.priority;
  const tasks = today?.task_queue || fallbackTaskQueue(d);
  const cards = today?.task_distribution || today?.cards || [
    { title: "紧急任务", value: 4, desc: "需要今天先处理" },
    { title: "今日到期", value: 3, desc: "有明确时间限制" },
    { title: "待确认", value: s.approval_required_count || safeArray(d.approval_required_tasks).length, desc: "确认前不执行" },
    { title: "可测试机会", value: s.traffic_experiment_count || traffic.experiment_count || 0, desc: "小范围观察" },
  ];
  const pendingCount = priority?.pending_count ?? s.approval_required_count ?? safeArray(d.approval_required_tasks).length;
  view().innerHTML = `<section class="hero-card dashboard-hero">
    <div>
      <p class="eyebrow">TASK BOARD</p>
      <h2>${priority?.title || "今日任务清单"}</h2>
    </div>
    <div class="hero-actions">
      <span>${today?.operating_unit?.name || s.unit_name || d.operating_unit?.unit_name || "-"}</span>
      <strong>${pendingCount} 项待确认</strong>
    </div>
  </section>
  <section class="kpi-grid">${cards.map((item) => card(item.title, `<strong>${item.value}</strong><span class="card-desc">${item.desc || ""}</span>`)).join("")}</section>
  <section class="page-section dashboard-queue">
    <div class="section-header">
      <h3>处理顺序</h3>
      <span class="status-badge">${today?.cycle?.frequency_label || cnFrequency(s.cycle_frequency || d.cycle_policy?.cycle_frequency)}</span>
    </div>
    ${renderTaskQueue(tasks)}
  </section>`;
}

async function renderOperatingUnit() {
  const d = raw();
  const fallback = {
    unit_name: d.operating_unit?.unit_name,
    unit_id: d.operating_unit?.operating_unit_id,
    dominant_product_group: d.operating_unit?.dominant_product_group,
    reason: d.operating_unit?.reason,
    product_group_summary: d.operating_unit?.product_group_summary || {},
    cycle_policy: d.cycle_policy || {},
  };
  const unit = await fetchProductView("/api/business/operating-unit", fallback);
  const policy = unit.cycle_policy || {};
  view().innerHTML = `<section class="page-section">
    ${kv([["经营单元", unit.unit_name || "-"], ["商品群", unit.dominant_product_group || "-"], ["频率", policy.frequency_label || cnFrequency(policy.frequency || policy.cycle_frequency)], ["时间", policy.run_time || "-"]])}
  </section>
  <section class="two-column">
    ${card("分布", list(Object.entries(unit.product_group_summary || {}).map(([key, value]) => `${key} · ${value}`)))}
    ${card("触发", list(policy.trigger_rules || []))}
  </section>`;
}

async function renderDataCheck() {
  if (state.apiMode) {
    try { state.importValidation = await fetchJson("/api/business/data-health"); } catch { state.importValidation = null; }
  }
  const validation = state.importValidation || { datasets: ["商品", "订单", "库存", "退款", "客户"].map((name) => ({ name, status: "ready" })) };
  const rows = safeArray(validation.datasets).map((item) => `<div><strong>${item.name || item.label}</strong>${statusBadge(item.status || "ready")}</div>`).join("");
  view().innerHTML = `<section class="page-section">
    <div class="section-header"><h3>数据健康</h3><button onclick="refreshCurrentView()">重新检查</button></div>
    <div class="table-like compact-table">${rows}</div>
  </section>`;
}

async function renderProducts() {
  const d = raw();
  const fallback = { title: "商品体检结果", summary: d.summary || {}, items: safeArray(d.product_diagnosis) };
  const payload = state.productsView || await fetchProductView("/api/business/products", fallback);
  state.productsView = payload;
  const rows = safeArray(payload.items).map((item) => `<div class="result-card"><h3>${item.product_name} ${badge(item.risk_level)}</h3>${kv([["库存", item.stock ?? "-"], ["毛利", item.gross_margin ?? "-"], ["活动毛利", item.activity_margin ?? "-"]])}${list(item.suggestions || item.suggested_actions || [])}</div>`).join("");
  view().innerHTML = `<section class="result-list">${rows || card("暂无商品体检", "<p>当前没有可展示的商品结果。</p>")}</section>`;
}

async function renderCompetitors() {
  const d = raw();
  const c = d.competitor_analysis || {};
  const fallback = {
    title: "竞品机会",
    category_name: c.category_name,
    competitor_count: c.competitor_count || 0,
    trigger_product: c.reference_product || {},
    price_gap: c.price_gap || {},
    bad_review_keywords: c.review_gap?.top_bad_review_keywords || [],
    opportunity_actions: c.review_gap?.opportunity_actions || [],
    next_action: c.next_action,
  };
  const payload = state.competitorsView || await fetchProductView("/api/business/competitors", fallback);
  state.competitorsView = payload;
  view().innerHTML = `<section class="page-section">
    ${kv([["触发商品", payload.trigger_product?.product_name || "-"], ["参考对象", payload.competitor_count || 0], ["价格", payload.price_gap?.position || "-"], ["动作", payload.next_action || "-"]])}
  </section>
  <section class="two-column">
    ${card("差评", list(payload.bad_review_keywords || []))}
    ${card("机会", list(payload.opportunity_actions || []))}
  </section>`;
}

async function renderListing() {
  const d = raw();
  const plan = d.listing_growth_plan || {};
  const draft = plan.listing_draft || {};
  const fallback = {
    title: "上新建议",
    candidate_count: plan.candidate_count || 0,
    top_candidate: plan.top_candidate || {},
    title_draft: draft.title_draft,
    image_plan: draft.image_plan || [],
    sku_plan: draft.sku_plan || [],
    compliance_checklist: draft.compliance_checklist || [],
    next_action: plan.next_action,
  };
  const payload = state.listingView || await fetchProductView("/api/business/listing", fallback);
  state.listingView = payload;
  const top = payload.top_candidate || {};
  view().innerHTML = `<section class="page-section">
    ${kv([["候选", top.product_name || "-"], ["评分", top.score || "-"], ["毛利", top.expected_margin ?? "-"], ["毛利率", top.margin_rate ?? "-"]])}
  </section>
  <section class="two-column">
    ${card("标题", `<div class="title-draft">${payload.title_draft || "-"}</div>`)}
    ${card("检查", list(payload.compliance_checklist || []))}
  </section>
  <section class="two-column">
    ${card("主图", list(payload.image_plan || []))}
    ${card("规格", list(payload.sku_plan || []))}
  </section>`;
}

async function renderTraffic() {
  const d = raw();
  const report = d.traffic_feedback_report || {};
  const fallback = {
    title: "流量复盘",
    experiment_count: report.experiment_count || 0,
    next_action: report.next_action,
    loopback_actions: report.loopback_actions || [],
    items: safeArray(report.diagnoses),
  };
  const payload = state.trafficView || await fetchProductView("/api/business/traffic", fallback);
  state.trafficView = payload;
  const rows = safeArray(payload.items).map((item) => `<div class="task-row"><strong>${item.product_id || item.experiment_id}</strong><span>${item.traffic_source || "-"}</span>${badge(item.risk_level)}<small>${item.decision_label || cnDecision(item.decision)}</small></div>`).join("");
  view().innerHTML = `<section class="page-section">${kv([["测试", payload.experiment_count || 0], ["结论", payload.next_action || "-"], ["回流", safeArray(payload.loopback_actions).join(" / ") || "-"], ["状态", "待确认"]])}</section><section class="task-table">${rows}</section>`;
}

async function renderApprovals() {
  let actions = [];
  if (state.apiMode) {
    try { actions = (await fetchJson("/api/business/actions")).items || []; } catch { actions = []; }
  }
  const d = raw();
  const tasks = actions.length ? actions : safeArray(d.approval_required_tasks?.length ? d.approval_required_tasks : d.rpa_tasks).map((task) => ({ action_id: task.task_id, action_name: task.task_type, risk_level: task.risk_level, suggestion: task.ai_suggestion }));
  const rows = tasks.map((task) => `<div class="result-card"><h3>${task.action_name || "动作"} ${badge(task.risk_level)}</h3><div class="action-line">${task.suggestion || "待确认"}</div><div class="task-actions"><button onclick="updateTask('${task.action_id}', 'approve')">确认</button><button class="secondary" onclick="updateTask('${task.action_id}', 'reject')">拒绝</button></div></div>`).join("");
  view().innerHTML = `<section class="result-list">${rows}</section>`;
}

async function renderReports() {
  if (state.apiMode && !state.reportText) {
    try { state.reportText = await (await fetch("/api/business/report")).text(); } catch { state.reportText = "暂无报告"; }
  }
  const summary = raw().summary || {};
  view().innerHTML = `<section class="page-section">${kv([["经营单元", summary.unit_name || "-"], ["频率", cnFrequency(summary.cycle_frequency)], ["重点", cnModule(summary.loop_next_module)], ["确认", summary.approval_required_count || 0]])}</section><section class="page-section"><div class="report-preview"><pre>${state.reportText || "暂无报告"}</pre></div></section>`;
}

async function updateTask(taskId, action) {
  if (!state.apiMode) return;
  const response = await fetch(`/api/approvals/${taskId}/${action}`, { method: "POST" });
  if (!response.ok) return;
  await refreshWorkflow();
  await renderApprovals();
}

async function refreshCurrentView() { await renderRoute(); }
async function refreshAndRender() { await refreshWorkflow(); await renderRoute(); }

window.updateTask = updateTask;
window.refreshCurrentView = refreshCurrentView;
window.refreshAndRender = refreshAndRender;

$("refreshBtn").addEventListener("click", refreshAndRender);
window.addEventListener("hashchange", renderRoute);
refreshAndRender();
