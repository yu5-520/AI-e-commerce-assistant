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
    approval_required_count: 7,
    loop_next_module: "crm_after_sales_diagnosis",
  },
  operating_unit: {
    unit_name: "家居生活商品",
    dominant_product_group: "home_living_goods",
    product_group_summary: { sun_protection_goods: 1, home_storage_goods: 1, health_home_goods: 1 },
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
  apiData: null,
  businessToday: null,
  apiMode: false,
  importValidation: null,
  reportText: "",
};

const routes = {
  dashboard: ["总览", renderDashboard],
  "operating-unit": ["经营单元", renderOperatingUnit],
  "data-check": ["数据", renderDataCheck],
  products: ["商品", renderProducts],
  competitors: ["竞品", renderCompetitors],
  listing: ["上新", renderListing],
  traffic: ["流量", renderTraffic],
  approvals: ["确认", renderApprovals],
  reports: ["报告", renderReports],
};

const $ = (id) => document.getElementById(id);
const view = () => $("appView");
const data = () => state.apiData || fallbackData;
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
const badge = (level) => `<span class="badge ${level || "low"}">${riskLabel(level)}</span>`;
const statusBadge = (status) => `<span class="status-badge ${status || "ready"}">${({ success: "完成", failed: "失败", running: "运行", approved: "确认", rejected: "拒绝", pending: "待定", preview: "演示", ready: "可用" }[status]) || status || "可用"}</span>`;
const card = (title, body, extra = "") => `<article class="card ${extra}"><h3>${title}</h3>${body}</article>`;
const list = (items) => `<ul class="clean-list">${safeArray(items).map((item) => `<li>${item}</li>`).join("")}</ul>`;
const kv = (items) => `<div class="info-list">${items.map(([key, value]) => `<div><span>${key}</span><strong>${value ?? "-"}</strong></div>`).join("")}</div>`;

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

async function refreshWorkflow() {
  try {
    const payload = await fetchJson("/api/business/today");
    state.businessToday = payload;
    state.apiData = payload.raw || fallbackData;
    state.apiMode = true;
    $("apiModeBadge").textContent = "在线";
    $("apiModeBadge").className = "mode-badge api";
  } catch {
    state.businessToday = null;
    state.apiData = fallbackData;
    state.apiMode = false;
    $("apiModeBadge").textContent = "演示";
    $("apiModeBadge").className = "mode-badge local";
  }
}

async function renderRoute() {
  const route = routes[location.hash.replace("#", "")] ? location.hash.replace("#", "") : "dashboard";
  document.querySelectorAll(".nav a").forEach((link) => link.classList.toggle("active", link.dataset.route === route));
  const [title, renderer] = routes[route];
  $("pageTitle").textContent = title;
  await renderer();
}

function renderDashboard() {
  const d = data();
  const today = state.businessToday;
  const s = d.summary || {};
  const loop = d.operating_loop_summary || {};
  const traffic = d.traffic_feedback_report || {};
  const priority = today?.priority;
  const cards = today?.cards || [
    { title: "经营单元", value: s.unit_name || "-" },
    { title: "商品", value: s.product_count || safeArray(d.product_diagnosis).length },
    { title: "流量", value: s.traffic_experiment_count || traffic.experiment_count || 0 },
    { title: "确认", value: s.approval_required_count || safeArray(d.approval_required_tasks).length },
  ];
  view().innerHTML = `<section class="hero-card">
    <div>
      <p class="eyebrow">PRIORITY</p>
      <h2>${priority?.title || cnModule(s.loop_next_module || loop.next_module)}</h2>
    </div>
    <div class="hero-actions">
      <span>${today?.operating_unit?.name || s.unit_name || d.operating_unit?.unit_name || "-"}</span>
      <strong>${today?.cycle?.frequency_label || cnFrequency(s.cycle_frequency || d.cycle_policy?.cycle_frequency)}</strong>
    </div>
  </section>
  <section class="kpi-grid">${cards.map((item) => card(item.title, `<strong>${item.value}</strong>`)).join("")}</section>
  <section class="two-column">
    ${card("下一步", list(priority?.next_steps || loop.next_iteration_plan || []))}
    ${card("边界", list(today?.boundaries || ["建议", "草案", "确认"]))}
  </section>`;
}

async function renderOperatingUnit() {
  let payload = null;
  if (state.apiMode) {
    try { payload = await fetchJson("/api/business/operating-unit"); } catch { payload = null; }
  }
  const d = data();
  const unit = payload || d.operating_unit || {};
  const policy = payload?.cycle_policy || d.cycle_policy || {};
  view().innerHTML = `<section class="page-section">
    ${kv([["经营单元", unit.unit_name || "-"], ["商品群", unit.dominant_product_group || "-"], ["频率", policy.frequency_label || cnFrequency(policy.cycle_frequency || policy.frequency)], ["时间", policy.run_time || "-"]])}
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
  view().innerHTML = `<section class="page-section"><div class="table-like compact-table">${rows}</div></section>`;
}

function renderProducts() {
  const rows = safeArray(data().product_diagnosis).map((item) => `<div class="result-card"><h3>${item.product_name} ${badge(item.risk_level)}</h3>${kv([["库存", item.stock ?? "-"], ["毛利", item.gross_margin ?? "-"], ["活动毛利", item.activity_margin ?? "-"]])}${list(safeArray(item.suggested_actions))}</div>`).join("");
  view().innerHTML = `<section class="result-list">${rows}</section>`;
}

function renderCompetitors() {
  const c = data().competitor_analysis || {};
  view().innerHTML = `<section class="page-section">
    ${kv([["触发商品", c.reference_product?.product_name || "-"], ["参考对象", c.competitor_count || 0], ["价格", c.price_gap?.position || "-"], ["动作", c.next_action || "-"]])}
  </section>
  <section class="two-column">
    ${card("差评", list(c.review_gap?.top_bad_review_keywords || []))}
    ${card("机会", list(c.review_gap?.opportunity_actions || []))}
  </section>`;
}

function renderListing() {
  const plan = data().listing_growth_plan || {};
  const top = plan.top_candidate || {};
  const draft = plan.listing_draft || {};
  view().innerHTML = `<section class="page-section">
    ${kv([["候选", top.product_name || "-"], ["评分", top.score || "-"], ["毛利", top.expected_margin ?? "-"], ["毛利率", top.margin_rate ?? "-"]])}
  </section>
  <section class="two-column">
    ${card("标题", `<div class="title-draft">${draft.title_draft || "-"}</div>`)}
    ${card("检查", list(draft.compliance_checklist || []))}
  </section>
  <section class="two-column">
    ${card("主图", list(draft.image_plan || []))}
    ${card("规格", list(draft.sku_plan || []))}
  </section>`;
}

function renderTraffic() {
  const report = data().traffic_feedback_report || {};
  const rows = safeArray(report.diagnoses).map((item) => `<div class="task-row"><strong>${item.product_id || item.experiment_id}</strong><span>${item.traffic_source || "-"}</span>${badge(item.risk_level)}<small>${cnDecision(item.decision)}</small></div>`).join("");
  view().innerHTML = `<section class="page-section">${kv([["测试", report.experiment_count || 0], ["结论", report.next_action || "-"], ["回流", safeArray(report.loopback_actions).join(" / ") || "-"], ["状态", "待确认"]])}</section><section class="task-table">${rows}</section>`;
}

async function renderApprovals() {
  let actions = [];
  if (state.apiMode) {
    try { actions = (await fetchJson("/api/business/actions")).items || []; } catch { actions = []; }
  }
  const d = data();
  const tasks = actions.length ? actions : safeArray(d.approval_required_tasks?.length ? d.approval_required_tasks : d.rpa_tasks).map((task) => ({ action_id: task.task_id, action_name: task.task_type, risk_level: task.risk_level, suggestion: task.ai_suggestion }));
  const rows = tasks.map((task) => `<div class="result-card"><h3>${task.action_name || "动作"} ${badge(task.risk_level)}</h3><div class="action-line">${task.suggestion || "待确认"}</div><div class="task-actions"><button onclick="updateTask('${task.action_id}', 'approve')">确认</button><button class="secondary" onclick="updateTask('${task.action_id}', 'reject')">拒绝</button></div></div>`).join("");
  view().innerHTML = `<section class="result-list">${rows}</section>`;
}

async function renderReports() {
  if (state.apiMode && !state.reportText) {
    try { state.reportText = await (await fetch("/api/business/report")).text(); } catch { state.reportText = "暂无报告"; }
  }
  const summary = data().summary || {};
  view().innerHTML = `<section class="page-section">${kv([["经营单元", summary.unit_name || "-"], ["频率", cnFrequency(summary.cycle_frequency)], ["重点", cnModule(summary.loop_next_module)], ["确认", summary.approval_required_count || 0]])}</section><section class="page-section"><div class="report-preview"><pre>${state.reportText || "暂无报告"}</pre></div></section>`;
}

async function importMockData() {
  if (!state.apiMode) return;
  await fetchJson("/api/data/import/mock", { method: "POST" });
  await renderDataCheck();
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

window.importMockData = importMockData;
window.updateTask = updateTask;
window.refreshCurrentView = refreshCurrentView;
window.refreshAndRender = refreshAndRender;

$("refreshBtn").addEventListener("click", refreshAndRender);
window.addEventListener("hashchange", renderRoute);
refreshAndRender();
