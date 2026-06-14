const fallbackData = {
  summary: {
    unit_name: "家居生活商品",
    operating_unit_id: "home_living_goods",
    cycle_frequency: "daily",
    cycle_type: "daily_fast_moving_goods_loop",
    product_count: 3,
    customer_count: 4,
    competitor_count: 4,
    listing_candidate_count: 4,
    traffic_experiment_count: 4,
    rpa_task_count: 7,
    approval_required_count: 7,
    auto_execution_allowed_count: 0,
    loop_status: "closed_loop_mock_ready",
    loop_next_module: "crm_after_sales_diagnosis",
    traffic_next_action: "优先处理高退款实验，进入售后归因，再决定是否继续投流。",
  },
  operating_unit: {
    unit_name: "家居生活商品",
    base_source: "ERP product data",
    dominant_product_group: "sun_protection_goods",
    reason: "根据商品类目、商品名称、主卖点、库存和订单结构，当前更像家居生活商品经营单元。",
    product_group_summary: { sun_protection_goods: 1, home_storage_goods: 1, health_home_goods: 1 },
    keyword_signals: { 家居: 2, 收纳: 1, 遮阳伞: 1, 办公室: 1 },
  },
  cycle_policy: {
    cycle_frequency: "daily",
    cycle_type: "daily_fast_moving_goods_loop",
    run_time: "09:00",
    report_type: "daily_operation_report",
    description: "家居生活商品属于低客单、高周转或季节性商品，适合每日生成经营日报和异常提醒。",
    trigger_rules: ["库存异常", "退款率异常", "ROI 低", "点击率异常", "转化率异常"],
  },
  product_diagnosis: [
    { product_id: "P001", product_name: "遮阳伞", risk_level: "medium", risks: ["库存高", "活动价风险"], suggested_actions: ["复核活动价利润", "小流量观察主图点击"], gross_margin: 8.2, activity_margin: 1.2, stock: 200 },
    { product_id: "P002", product_name: "厨房置物架", risk_level: "medium", risks: ["库存偏高", "转化承接需观察"], suggested_actions: ["补充安装说明", "检查尺寸和承重表达"], gross_margin: 12.4, activity_margin: 6.4, stock: 120 },
    { product_id: "P003", product_name: "护腰坐垫", risk_level: "high", risks: ["退款异常", "体验预期差异"], suggested_actions: ["进入售后归因", "优化材质和尺寸说明"], gross_margin: 11.5, activity_margin: 5.5, stock: 80 },
  ],
  customer_segmentation: [
    { customer_id: "C001", segment: "高价值客户", risk_level: "low", tags: ["高价值", "复购潜力"], recommended_actions: ["生成老客复购任务草案"] },
    { customer_id: "C004", segment: "售后敏感客户", risk_level: "high", tags: ["售后敏感", "流失风险"], recommended_actions: ["优先做售后归因", "不直接营销触达"] },
  ],
  competitor_analysis: {
    category_name: "家居生活商品",
    competitor_count: 4,
    data_source: "examples/category_home_living/mock_competitors.csv",
    reference_product: { product_id: "P003", product_name: "护腰坐垫", trigger_reason: "退款异常，优先比对竞品差评、卖点承诺和售后问题。" },
    price_gap: { position: "within_market", insight: "当前价格处在可测试区间，重点看评价、主图和详情页承接。" },
    review_gap: { top_bad_review_keywords: ["尺寸不符", "材质偏软", "支撑不明显"], opportunity_actions: ["补充尺寸参照", "明确材质和支撑预期", "优化售后说明"] },
    next_action: "优先优化尺寸说明、SKU 承接和客服引导，再进入下一轮流量测试。",
  },
  listing_growth_plan: {
    category_name: "家居生活商品",
    candidate_count: 4,
    top_candidate: { supplier_product_id: "SHL002", product_name: "免打孔厨房置物架", score: 89, expected_margin: 35, margin_rate: 0.5932, reasons: ["符合当前经营单元", "库存承接能力较好", "匹配收纳和节省空间卖点"], risks: ["安装咨询较多，需补充安装说明"] },
    listing_draft: { title_draft: "免打孔厨房置物架 收纳 节省空间 免安装 家用多场景实用款", image_plan: ["第一屏突出使用场景、功能利益和规格信息。", "补充尺寸、材质、安装方式、承重或使用限制。"], sku_plan: ["先保留 2-4 个主推规格或尺寸。", "组合款要复核物流成本和包装体积。"], compliance_checklist: ["不使用绝对承重、永久耐用等无依据表达。", "真实上架、改价、活动报名和投放必须人工确认。"] },
    next_action: "人工复核候选评分、利润安全线、规格说明、主图方向和上新检查表，再进入小流量测试计划。",
  },
  traffic_feedback_report: {
    experiment_count: 4,
    decision_summary: { enter_after_sales_diagnosis: 1, stop_or_reduce_budget: 1, continue_testing: 1 },
    risk_summary: { medium: 2, high: 1, low: 1 },
    next_action: "优先处理高退款实验，进入售后归因，再决定是否继续投流。",
    loopback_actions: ["回流到 CRM / 售后判断：标记高退款实验，进入尺寸、材质、物流和客服 SOP 归因。", "回流到经营判断：标记 ROI 低，暂停放量并要求人工复核预算策略。"],
    diagnoses: [
      { experiment_id: "THL001", product_id: "P001", title_version: "遮阳伞主图A", traffic_source: "自然搜索", click_rate: 0.034, conversion_rate: 0.0686, refund_rate: 0.0571, roi: 1.7, decision: "continue_testing", risk_level: "low", recommended_actions: ["测试指标相对健康，可继续观察或小幅扩大测试"] },
      { experiment_id: "THL003", product_id: "P003", title_version: "护腰坐垫主图A", traffic_source: "付费测试", click_rate: 0.0265, conversion_rate: 0.0333, refund_rate: 0.3333, roi: 0.72, decision: "enter_after_sales_diagnosis", risk_level: "high", recommended_actions: ["成交后退款偏高，优先进入尺寸、材质和客服归因"] },
    ],
  },
  operating_loop_summary: {
    loop_status: "closed_loop_mock_ready",
    next_module: "crm_after_sales_diagnosis",
    next_iteration_plan: ["优先处理高退款和售后敏感问题。", "复查尺寸、材质、物流、客服话术和卖点承诺。", "售后归因完成前，不建议继续放量。"],
    manual_review_required: true,
    auto_execution_allowed: false,
  },
  rpa_tasks: [
    { task_id: "TASK_PRODUCT_DAILY_001", task_type: "经营日报", risk_level: "low", approval_status: "pending", auto_execution_allowed: false, ai_suggestion: "生成今日商品经营日报和下一轮复盘摘要。" },
    { task_id: "TASK_SKU_PRICE_001", task_type: "价格复核", risk_level: "medium", approval_status: "pending", auto_execution_allowed: false, ai_suggestion: "生成价格复核表，标记保本线、活动价风险和人工确认项。" },
    { task_id: "TASK_CRM_AFTER_SALES_004", task_type: "售后归因", risk_level: "high", approval_status: "pending", auto_execution_allowed: false, ai_suggestion: "生成售后归因表，先查尺寸、材质、物流和客服承诺。" },
  ],
  approval_required_tasks: [],
  rag_context: {
    category_profile: [{ source: "经营单元档案", snippet: "家居生活商品应重点观察价格带、规格尺寸、安装说明、材质承诺、物流包装和售后反馈。" }],
    traffic_feedback: [{ source: "经营复盘规则", snippet: "点击低看标题主图，转化低看价格和详情页，退款高先查售后归因，ROI 低先止损。" }],
  },
};
fallbackData.approval_required_tasks = fallbackData.rpa_tasks;

const fallbackImportStatus = {
  status: "preview",
  datasets: ["商品表", "订单表", "库存表", "退款表", "客户表", "客户标签", "互动记录"].map((label) => ({ label, filename: "演示数据", row_count: 0, status: "preview" })),
  relationship_checks: [],
};

const state = {
  apiData: null,
  apiMode: false,
  importValidation: null,
  importRecords: [],
  tasks: [],
  approvalRecords: [],
  reportRecords: [],
  reportText: "",
};

const routes = {
  dashboard: ["今日总览", "先看今天该盯什么、该停什么、该确认什么。", renderDashboard],
  "operating-unit": ["经营单元", "系统根据商品结构识别当前生意类型，并给出适合的运行频率。", renderOperatingUnit],
  "data-check": ["数据体检", "确认商品、订单、库存、退款和客户数据是否足够支撑判断。", renderDataCheck],
  products: ["商品体检", "找到库存、利润、退款和售后承诺里的经营风险。", renderProducts],
  competitors: ["竞品机会", "只看同经营单元里的价格、卖点、规格和差评机会。", renderCompetitors],
  listing: ["上新建议", "从货盘里找值得测试的商品，并生成上新资料草案。", renderListing],
  traffic: ["流量复盘", "看点击、转化、退款和投入产出，决定下一轮怎么调。", renderTraffic],
  approvals: ["待确认动作", "所有涉及上架、改价、投放、客户触达的动作，都先放到这里确认。", renderApprovals],
  reports: ["经营报告", "把本轮判断、机会、风险和下一步动作整理成一份报告。", renderReports],
};

const $ = (id) => document.getElementById(id);
const view = () => $("appView");
const data = () => state.apiData || fallbackData;
const safeArray = (value) => Array.isArray(value) ? value : [];
const first = (value, fallback = {}) => Array.isArray(value) && value.length ? value[0] : fallback;
const cnFrequency = (frequency) => ({ daily: "每天", weekly: "每周", monthly: "每月" }[frequency] || frequency || "未设置");
const cnDecision = (decision) => ({
  enter_after_sales_diagnosis: "先查售后",
  stop_or_reduce_budget: "先止损",
  change_title_or_main_image: "换标题/主图",
  adjust_sku_price_or_detail_page: "调规格/价格",
  scale_carefully: "谨慎放量",
  continue_testing: "继续观察",
}[decision] || decision || "继续观察");
const cnModule = (module) => ({
  crm_after_sales_diagnosis: "售后归因",
  erp_profit_and_budget_review: "利润与预算复核",
  competitor_title_image_review: "标题 / 主图复查",
  listing_sku_pricing_review: "规格 / 定价复查",
  erp_product_risk_review: "商品风险复查",
  controlled_scale_review: "小幅放量复核",
  continue_operating_loop: "继续循环",
}[module] || module || "继续循环");

const badge = (level) => `<span class="badge ${level || "low"}">${level === "high" ? "重点风险" : level === "medium" ? "需要关注" : "状态正常"}</span>`;
const statusBadge = (status) => `<span class="status-badge ${status || "preview"}">${({ success: "已完成", failed: "失败", running: "生成中", approved: "已确认", rejected: "已拒绝", pending: "待确认", preview: "演示", passed: "通过", warning: "注意", markdown: "报告" }[status]) || status || "演示"}</span>`;
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
    state.apiData = await fetchJson("/api/demo/run");
    state.apiMode = true;
    $("apiModeBadge").textContent = "已连接经营数据";
    $("apiModeBadge").className = "mode-badge api";
  } catch (error) {
    state.apiData = fallbackData;
    state.apiMode = false;
    $("apiModeBadge").textContent = "本地演示数据";
    $("apiModeBadge").className = "mode-badge local";
  }
}

async function renderRoute() {
  const route = routes[location.hash.replace("#", "")] ? location.hash.replace("#", "") : "dashboard";
  document.querySelectorAll(".nav a").forEach((link) => link.classList.toggle("active", link.dataset.route === route));
  const [title, subtitle, renderer] = routes[route];
  $("pageTitle").textContent = title;
  $("pageSubtitle").textContent = subtitle;
  await renderer();
}

function renderDashboard() {
  const d = data();
  const s = d.summary || {};
  const loop = d.operating_loop_summary || {};
  const traffic = d.traffic_feedback_report || {};
  view().innerHTML = `<section class="hero-card">
    <div>
      <p class="eyebrow">今天优先看</p>
      <h2>${cnModule(s.loop_next_module || loop.next_module)}</h2>
      <p>${traffic.next_action || "先完成商品、竞品、上新和流量复盘，再生成下一轮动作。"}</p>
    </div>
    <div class="hero-actions">
      <span>${s.unit_name || d.operating_unit?.unit_name || "经营单元待识别"}</span>
      <strong>${cnFrequency(s.cycle_frequency || d.cycle_policy?.cycle_frequency)}循环</strong>
    </div>
  </section>
  <section class="kpi-grid">
    ${card("经营单元", `<strong>${s.unit_name || "-"}</strong><p>由商品结构自动识别</p>`)}
    ${card("商品体检", `<strong>${s.product_count || safeArray(d.product_diagnosis).length}</strong><p>已检查商品</p>`)}
    ${card("流量测试", `<strong>${s.traffic_experiment_count || traffic.experiment_count || 0}</strong><p>已复盘测试</p>`)}
    ${card("待确认", `<strong>${s.approval_required_count || safeArray(d.approval_required_tasks).length}</strong><p>高风险动作不自动执行</p>`)}
  </section>
  <section class="two-column">
    ${card("下一轮计划", list(loop.next_iteration_plan || ["复查售后归因", "再决定是否继续投流", "所有关键动作人工确认"]))}
    ${card("使用边界", list(["只生成判断、草案和报告", "不自动上架、改价、投放", "不自动触达客户或退款", "确认后再进入下一步"]))}
  </section>`;
}

function renderOperatingUnit() {
  const d = data();
  const unit = d.operating_unit || {};
  const policy = d.cycle_policy || {};
  view().innerHTML = `<section class="page-section">
    <div class="section-header"><div><h2>系统识别出的生意类型</h2><p class="muted">不是预设防晒服，而是先看你的商品结构。</p></div>${statusBadge("success")}</div>
    ${kv([["经营单元", unit.unit_name || "-"], ["主要商品群", unit.dominant_product_group || "-"], ["运行频率", cnFrequency(policy.cycle_frequency)], ["报告类型", policy.report_type || "-"]])}
    <p class="callout">${unit.reason || "系统会根据商品名称、类目、库存和订单判断当前经营单元。"}</p>
  </section>
  <section class="two-column">
    ${card("商品群分布", list(Object.entries(unit.product_group_summary || {}).map(([key, value]) => `${key}：${value} 个商品`)))}
    ${card("触发提醒", list(policy.trigger_rules || []))}
  </section>`;
}

async function renderDataCheck() {
  if (state.apiMode) {
    try {
      state.importValidation = await fetchJson("/api/data/validate", { method: "POST" });
      state.importRecords = await fetchJson("/api/data/imports");
    } catch {
      state.importValidation = fallbackImportStatus;
      state.importRecords = [];
    }
  } else {
    state.importValidation = fallbackImportStatus;
    state.importRecords = [];
  }
  const validation = state.importValidation || fallbackImportStatus;
  const datasetRows = safeArray(validation.datasets).map((item) => `<div><strong>${item.label || item.dataset_name}</strong><span>${item.row_count ?? 0} 行数据</span>${statusBadge(item.status)}</div>`).join("");
  view().innerHTML = `<section class="page-section"><div class="section-header"><div><h2>数据是否够用</h2><p class="muted">先确认商品、订单、库存、退款和客户数据能不能支撑经营判断。</p></div><div class="button-group"><button onclick="refreshCurrentView()">重新检查</button><button class="secondary" onclick="importMockData()">保存本轮演示数据</button></div></div><div class="table-like compact-table">${datasetRows}</div></section>`;
}

function renderProducts() {
  const cards = safeArray(data().product_diagnosis).map((item) => `<div class="result-card"><h3>${item.product_name} ${badge(item.risk_level)}</h3>${kv([["库存", item.stock ?? "-"], ["毛利", item.gross_margin ?? "-"], ["活动后毛利", item.activity_margin ?? "-"]])}<p>发现：${safeArray(item.risks).join("，") || "暂无明显风险"}</p><p>建议：${safeArray(item.suggested_actions).join("；") || "继续观察"}</p></div>`).join("");
  view().innerHTML = `<section class="page-section"><h2>商品体检结果</h2><p class="muted">优先处理库存高、利润薄、退款异常和承诺不清的商品。</p><div class="result-list">${cards}</div></section>`;
}

function renderCompetitors() {
  const c = data().competitor_analysis || {};
  view().innerHTML = `<section class="page-section"><div class="section-header"><div><h2>竞品机会</h2><p class="muted">只拆解同经营单元里的机会，不复制素材。</p></div><strong>${c.competitor_count || 0} 个参考对象</strong></div>
    ${kv([["触发商品", `${c.reference_product?.product_name || "-"}`], ["触发原因", c.reference_product?.trigger_reason || "-"], ["价格位置", c.price_gap?.position || "-"], ["下一步", c.next_action || "-"]])}
  </section>
  <section class="two-column">
    ${card("差评里看到的机会", list(c.review_gap?.top_bad_review_keywords || []))}
    ${card("可以补的动作", list(c.review_gap?.opportunity_actions || []))}
  </section>`;
}

function renderListing() {
  const plan = data().listing_growth_plan || {};
  const top = plan.top_candidate || {};
  const draft = plan.listing_draft || {};
  view().innerHTML = `<section class="page-section"><div class="section-header"><div><h2>最值得测试的上新候选</h2><p class="muted">先生成草案，不直接上架。</p></div><strong>${top.score || "-"} 分</strong></div>
    ${kv([["候选商品", top.product_name || "-"], ["预估毛利", top.expected_margin ?? "-"], ["毛利率", top.margin_rate ?? "-"], ["建议", plan.next_action || "-"]])}
  </section>
  <section class="two-column">
    ${card("上新标题草案", `<p>${draft.title_draft || "暂无"}</p>`)}
    ${card("上架前检查", list(draft.compliance_checklist || []))}
  </section>
  <section class="two-column">
    ${card("主图方向", list(draft.image_plan || []))}
    ${card("规格建议", list(draft.sku_plan || []))}
  </section>`;
}

function renderTraffic() {
  const report = data().traffic_feedback_report || {};
  const rows = safeArray(report.diagnoses).map((item) => `<div class="task-row"><div><strong>${item.product_id || item.experiment_id}</strong><p>${safeArray(item.recommended_actions).join("；") || "继续观察"}</p></div><span>${item.traffic_source || "测试流量"}</span>${badge(item.risk_level)}<small>${cnDecision(item.decision)}</small></div>`).join("");
  view().innerHTML = `<section class="page-section"><div class="section-header"><div><h2>流量复盘结论</h2><p class="muted">不直接加预算，先看点击、转化、退款和投入产出。</p></div><strong>${report.experiment_count || 0} 组测试</strong></div><p class="callout">${report.next_action || "继续收集测试数据。"}</p></section><section class="page-section"><h2>测试明细</h2><div class="task-table">${rows}</div></section><section class="page-section"><h2>回流到哪里</h2>${list(report.loopback_actions || [])}</section>`;
}

async function renderApprovals() {
  const d = data();
  try { state.approvalRecords = state.apiMode ? await fetchJson("/api/approvals/records") : []; } catch { state.approvalRecords = []; }
  const tasks = safeArray(d.approval_required_tasks?.length ? d.approval_required_tasks : d.rpa_tasks);
  const cards = tasks.map((task) => `<div class="result-card"><h3>${task.task_type || "待确认动作"} ${badge(task.risk_level)}</h3><p>${task.ai_suggestion || "请人工确认后再执行。"}</p><div class="task-actions"><button onclick="updateTask('${task.task_id}', 'approve')">确认执行</button><button class="secondary" onclick="updateTask('${task.task_id}', 'reject')">暂不执行</button></div></div>`).join("");
  view().innerHTML = `<section class="page-section"><h2>待确认动作</h2><p class="muted">系统只把建议放到这里，你确认后才进入下一步。</p><div class="result-list">${cards}</div></section>`;
}

async function renderReports() {
  try {
    const payload = state.apiMode ? await fetchJson("/api/reports") : { reports: [] };
    state.reportRecords = payload.reports || [];
  } catch { state.reportRecords = []; }
  if (state.apiMode && !state.reportText) {
    try { state.reportText = await (await fetch("/api/reports/demo")).text(); } catch { state.reportText = "经营报告暂时读取失败。"; }
  }
  const summary = data().summary || {};
  view().innerHTML = `<section class="page-section"><div class="section-header"><div><h2>本轮经营报告</h2><p class="muted">适合发给老板或运营自己复盘。</p></div><button onclick="refreshAndRender()">重新生成</button></div>${kv([["经营单元", summary.unit_name || "-"], ["循环频率", cnFrequency(summary.cycle_frequency)], ["下一步重点", cnModule(summary.loop_next_module)], ["待确认动作", summary.approval_required_count || 0]])}</section><section class="page-section"><h2>报告预览</h2><div class="report-preview"><pre>${state.reportText || "运行后会生成本轮经营报告。"}</pre></div></section>`;
}

async function importMockData() {
  if (!state.apiMode) return alert("当前是本地演示数据，启动后端服务后可以保存导入记录。");
  await fetchJson("/api/data/import/mock", { method: "POST" });
  await renderDataCheck();
}
async function updateTask(taskId, action) {
  if (!state.apiMode) return alert("当前是本地演示数据，启动后端服务后可以记录确认结果。");
  const response = await fetch(`/api/approvals/${taskId}/${action}`, { method: "POST" });
  if (!response.ok) return alert("动作确认失败，请稍后再试。");
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
