const fallbackData = {
  summary: {
    unit_name: "家居生活商品",
    cycle_frequency: "daily",
    approval_required_count: 13,
    traffic_experiment_count: 4,
    listing_candidate_count: 4,
    loop_next_module: "crm_after_sales_diagnosis",
  },
  operating_unit: { unit_name: "家居生活商品", operating_unit_id: "home_living_goods" },
  cycle_policy: { cycle_frequency: "daily", run_time: "09:00" },
  product_diagnosis: [
    { product_id: "P001", product_name: "遮阳伞", risk_level: "medium", suggested_actions: ["复核活动价", "观察主图点击"], gross_margin: 8.2, activity_margin: 1.2, stock: 200 },
    { product_id: "P002", product_name: "厨房置物架", risk_level: "medium", suggested_actions: ["补安装说明", "检查尺寸承重"], gross_margin: 12.4, activity_margin: 6.4, stock: 120 },
    { product_id: "P003", product_name: "护腰坐垫", risk_level: "high", suggested_actions: ["售后归因", "优化材质尺寸说明"], gross_margin: 11.5, activity_margin: 5.5, stock: 80 },
  ],
  competitor_analysis: {
    competitor_count: 4,
    reference_product: { product_name: "护腰坐垫" },
    price_gap: { position: "within_market" },
    review_gap: { top_bad_review_keywords: ["尺寸不符", "材质偏软", "支撑不明显"], opportunity_actions: ["补尺寸参照", "明确材质", "优化售后说明"] },
    next_action: "优化尺寸与客服承接",
  },
  listing_growth_plan: {
    candidate_count: 4,
    top_candidate: { product_name: "免打孔厨房置物架", score: 89, expected_margin: 35, margin_rate: "59%" },
    listing_draft: { title_draft: "免打孔厨房置物架 收纳 节省空间 家用多场景款", image_plan: ["场景图", "尺寸图", "安装图"], sku_plan: ["基础款", "升级款"], compliance_checklist: ["复核承重", "复核成本", "人工确认"] },
  },
  traffic_feedback_report: {
    experiment_count: 4,
    next_action: "先查售后",
    loopback_actions: ["售后归因", "预算止损"],
    diagnoses: [
      { experiment_id: "THL001", product_id: "P001", traffic_source: "自然搜索", decision: "continue_testing", risk_level: "low" },
      { experiment_id: "THL003", product_id: "P003", traffic_source: "付费测试", decision: "enter_after_sales_diagnosis", risk_level: "high" },
    ],
  },
  operating_loop_summary: { next_iteration_plan: ["售后归因", "复核尺寸材质", "暂停放量"] },
  rpa_tasks: [
    { task_id: "TASK_PRODUCT_DAILY_001", task_type: "经营日报", risk_level: "low", ai_suggestion: "生成经营日报" },
    { task_id: "TASK_SKU_PRICE_001", task_type: "价格复核", risk_level: "medium", ai_suggestion: "复核价格与保本线" },
    { task_id: "TASK_CRM_AFTER_SALES_004", task_type: "售后归因", risk_level: "high", ai_suggestion: "检查尺寸、材质、物流" },
  ],
};
fallbackData.approval_required_tasks = fallbackData.rpa_tasks;

const reportManagerPayload = {
  title: "ERP / CRM 报表管理",
  subtitle: "统一查看商品、订单、库存、退款和客户报表，支撑任务清单和经营判断。",
  metrics: [
    { label: "已接入系统", value: "2", desc: "ERP / CRM Mock" },
    { label: "报表数量", value: "7", desc: "商品、订单、库存、售后、客户" },
    { label: "最近同步", value: "实时", desc: "接口返回" },
    { label: "待接入", value: "聚水潭", desc: "多店铺汇总" },
  ],
  groups: [
    {
      title: "ERP 报表",
      reports: [
        { id: "products", name: "商品报表", source: "ERP", status: "已同步", count: "128 条", desc: "商品、库存、成本、售价、毛利率" },
        { id: "orders", name: "订单报表", source: "ERP", status: "已同步", count: "932 条", desc: "订单金额、发货状态、下单时间" },
        { id: "inventory", name: "库存报表", source: "ERP", status: "已同步", count: "128 条", desc: "库存数量、预警、补货状态" },
      ],
    },
    {
      title: "CRM 报表",
      reports: [
        { id: "refunds", name: "退款报表", source: "CRM", status: "已同步", count: "37 条", desc: "退款原因、售后状态、责任归因" },
        { id: "customers", name: "客户报表", source: "CRM", status: "已同步", count: "584 人", desc: "客户来源、复购、风险标记" },
        { id: "tags", name: "客户标签报表", source: "CRM", status: "已同步", count: "9 类", desc: "复购、价格敏感、售后敏感" },
        { id: "interactions", name: "客户互动报表", source: "CRM", status: "已同步", count: "216 条", desc: "咨询、评价、售后沟通" },
      ],
    },
  ],
  details: {
    products: { title: "商品报表", source: "ERP", summary: [["商品数", "128"], ["高风险商品", "3"], ["库存异常", "8"], ["售后敏感", "4"]], columns: ["商品ID", "商品名称", "平台", "店铺", "库存", "成本", "售价", "毛利率", "状态"], rows: [["P001", "遮阳伞", "淘宝", "家居生活主店", "200", "18", "39", "53%", "正常"], ["P002", "厨房置物架", "拼多多", "家居百货店", "120", "22", "49", "55%", "库存偏高"], ["P003", "护腰坐垫", "抖音小店", "家居好物号", "80", "35", "69", "49%", "售后敏感"]] },
    orders: { title: "订单报表", source: "ERP", summary: [["今日订单", "86"], ["已发货", "61"], ["待发货", "18"], ["退款中", "7"]], columns: ["订单号", "平台", "店铺", "商品", "金额", "状态", "下单时间"], rows: [["O001", "淘宝", "家居生活主店", "遮阳伞", "39", "已发货", "10:24"], ["O002", "拼多多", "家居百货店", "厨房置物架", "49", "待发货", "11:06"], ["O003", "抖音小店", "家居好物号", "护腰坐垫", "69", "退款中", "11:42"]] },
    inventory: { title: "库存报表", source: "ERP", summary: [["SKU 数", "128"], ["库存偏高", "8"], ["库存偏低", "5"], ["待补货", "3"]], columns: ["SKU", "商品", "平台", "店铺", "库存", "安全库存", "状态"], rows: [["SKU001", "遮阳伞", "淘宝", "家居生活主店", "200", "80", "库存偏高"], ["SKU002", "厨房置物架", "拼多多", "家居百货店", "120", "60", "正常"], ["SKU003", "护腰坐垫", "抖音小店", "家居好物号", "80", "100", "待补货"]] },
    refunds: { title: "退款报表", source: "CRM", summary: [["退款记录", "37"], ["尺码问题", "9"], ["材质问题", "6"], ["物流问题", "4"]], columns: ["退款ID", "平台", "商品", "金额", "原因", "状态", "处理建议"], rows: [["R001", "抖音小店", "护腰坐垫", "69", "材质偏软", "处理中", "补充材质说明"], ["R002", "淘宝", "遮阳伞", "39", "物流延迟", "已完成", "复查物流承诺"], ["R003", "拼多多", "厨房置物架", "49", "尺寸不符", "处理中", "补尺寸参照图"]] },
    customers: { title: "客户报表", source: "CRM", summary: [["客户数", "584"], ["复购客户", "96"], ["售后敏感", "23"], ["高价值", "41"]], columns: ["客户ID", "来源平台", "最近购买", "消费金额", "标签", "状态"], rows: [["C001", "淘宝", "遮阳伞", "156", "复购", "正常"], ["C002", "拼多多", "厨房置物架", "49", "价格敏感", "观察"], ["C003", "抖音小店", "护腰坐垫", "69", "售后敏感", "需跟进"]] },
    tags: { title: "客户标签报表", source: "CRM", summary: [["标签数", "9"], ["复购", "96"], ["价格敏感", "141"], ["售后敏感", "23"]], columns: ["标签", "人数", "来源", "用途", "建议动作"], rows: [["复购", "96", "订单", "活动触达", "优先推荐套装"], ["价格敏感", "141", "咨询/订单", "优惠判断", "控制折扣边界"], ["售后敏感", "23", "退款/互动", "客服承接", "人工复核话术"]] },
    interactions: { title: "客户互动报表", source: "CRM", summary: [["互动数", "216"], ["咨询", "132"], ["评价", "51"], ["售后", "33"]], columns: ["互动ID", "平台", "客户", "类型", "内容摘要", "处理状态"], rows: [["I001", "淘宝", "C001", "咨询", "询问遮阳伞尺寸", "已回复"], ["I002", "拼多多", "C002", "评价", "置物架安装反馈", "已记录"], ["I003", "抖音小店", "C003", "售后", "护腰坐垫支撑不足", "待跟进"]] },
  },
};

const state = { rawWorkflow: fallbackData, businessToday: null, apiMode: false, reportText: "", productsView: null, competitorsView: null, listingView: null, trafficView: null };
const routes = { dashboard: ["总览", renderDashboard], "operating-unit": ["经营单元", renderOperatingUnit], "data-check": ["ERP / CRM 报表管理", renderReportManager], "business-products": ["商品", renderProducts], "business-competitors": ["竞品", renderCompetitors], "business-listing": ["上新", renderListing], "business-traffic": ["流量", renderTraffic], "business-actions": ["确认", renderApprovals], "business-report": ["报告", renderReports] };
const legacyRouteMap = { products: "business-products", competitors: "business-competitors", listing: "business-listing", traffic: "business-traffic", approvals: "business-actions", reports: "business-report" };
const $ = (id) => document.getElementById(id);
const view = () => $("appView");
const raw = () => state.rawWorkflow || fallbackData;
const safeArray = (value) => Array.isArray(value) ? value : [];
const cnFrequency = (frequency) => ({ daily: "每日", weekly: "每周", monthly: "每月" }[frequency] || frequency || "未设定");
const cnDecision = (decision) => ({ enter_after_sales_diagnosis: "售后", stop_or_reduce_budget: "止损", continue_testing: "观察", scale_carefully: "放量" }[decision] || decision || "观察");
const cnModule = (module) => ({ crm_after_sales_diagnosis: "售后归因", continue_operating_loop: "继续循环" }[module] || module || "继续循环");
const riskLabel = (level) => ({ high: "高", medium: "中", low: "低" }[level] || "低");
const urgencyLabel = (level) => ({ high: "紧急", medium: "中", low: "观察" }[level] || "观察");
const badge = (level) => `<span class="badge ${level || "low"}">${riskLabel(level)}</span>`;
const urgencyBadge = (level, label) => `<span class="badge ${level || "low"}">${label || urgencyLabel(level)}</span>`;
const statusBadge = (status) => `<span class="status-badge ${status || "ready"}">${({ passed: "通过", success: "完成", failed: "失败", running: "运行", approved: "确认", rejected: "拒绝", pending: "待定", preview: "演示", ready: "可用" }[status]) || status || "可用"}</span>`;
const card = (title, body, extra = "") => `<article class="card ${extra}"><h3>${title}</h3>${body}</article>`;
const list = (items) => `<ul class="clean-list">${safeArray(items).map((item) => `<li>${item}</li>`).join("")}</ul>`;
const kv = (items) => `<div class="info-list">${items.map(([key, value]) => `<div><span>${key}</span><strong>${value ?? "-"}</strong></div>`).join("")}</div>`;
function formatDashboardTime(date = new Date()) { const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]; return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]} · ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")} 更新`; }
async function fetchJson(url, options = {}) { const response = await fetch(url, options); if (!response.ok) throw new Error(`${url} ${response.status}`); return response.json(); }
async function fetchProductView(url, fallbackValue) { if (!state.apiMode) return fallbackValue; try { return await fetchJson(url); } catch { return fallbackValue; } }
async function refreshWorkflow() { try { const payload = await fetchJson("/api/business/today"); state.businessToday = payload; state.rawWorkflow = payload.raw || fallbackData; state.apiMode = true; state.reportText = ""; state.productsView = null; state.competitorsView = null; state.listingView = null; state.trafficView = null; $("apiModeBadge").textContent = "在线"; $("apiModeBadge").className = "mode-badge api"; } catch { state.businessToday = null; state.rawWorkflow = fallbackData; state.apiMode = false; $("apiModeBadge").textContent = "演示"; $("apiModeBadge").className = "mode-badge local"; } }
async function renderRoute() { const hash = location.hash.replace("#", ""); const route = routes[hash] ? hash : (legacyRouteMap[hash] || "dashboard"); document.querySelectorAll(".nav a").forEach((link) => link.classList.toggle("active", link.dataset.route === route)); const [title, renderer] = routes[route]; $("pageTitle").textContent = title; await renderer(); }
function fallbackTaskQueue(d) { const s = d.summary || {}; const traffic = d.traffic_feedback_report || {}; return [ { rank: 1, title: "复查高退款商品", urgency: "紧急", urgency_level: "high", deadline: "今天 18:00 前", count: 3, impact: "退款率 / 评分", reason: "退款异常商品需要先复查尺码、材质、物流和客服承诺。" }, { rank: 2, title: "确认售后敏感问题", urgency: "紧急", urgency_level: "high", deadline: "今天内", count: 1, impact: "客服承接", reason: "售后问题未归因前，不建议继续放量。" }, { rank: 3, title: "小范围流量测试", urgency: "中", urgency_level: "medium", deadline: "明天 12:00 前", count: s.traffic_experiment_count || traffic.experiment_count || 0, impact: "ROI / 库存承接", reason: "继续小幅测试，但必须观察退款率、ROI 和库存承接。" }, { rank: 4, title: "上新前确认素材", urgency: "中", urgency_level: "medium", deadline: "明天内", count: s.listing_candidate_count || 0, impact: "转化率", reason: "确认后再进入下一步。" } ]; }
function renderTaskQueue(tasks) { return `<section class="dashboard-task-list">${safeArray(tasks).map((task, index) => `<article class="dashboard-task-card"><div class="task-rank">${task.rank || index + 1}</div><div class="task-main"><h3>${task.title || task.task_type || "待处理任务"}</h3><div class="task-meta">${urgencyBadge(task.urgency_level || task.risk_level, task.urgency)}<span>${task.deadline || "待定"}</span><span>${task.count ?? 1} 项</span><span>${task.impact || "经营承接"}</span></div><p>${task.reason || task.ai_suggestion || task.suggestion || "确认后再进入下一步。"}</p></div></article>`).join("")}</section>`; }
function renderDashboard() { const d = raw(); const today = state.businessToday; const s = d.summary || {}; const traffic = d.traffic_feedback_report || {}; const priority = today?.priority; const tasks = today?.task_queue || fallbackTaskQueue(d); const cards = today?.task_distribution || today?.cards || [ { title: "紧急任务", value: 4, desc: "需要先处理" }, { title: "到期任务", value: 3, desc: "有时间限制" }, { title: "待确认", value: s.approval_required_count || safeArray(d.approval_required_tasks).length, desc: "确认前不执行" }, { title: "可测试机会", value: s.traffic_experiment_count || traffic.experiment_count || 0, desc: "小范围观察" } ]; const unitName = today?.operating_unit?.name || s.unit_name || d.operating_unit?.unit_name || "-"; const pendingCount = priority?.pending_count ?? s.approval_required_count ?? 0; const cycleLabel = today?.cycle?.frequency_label || cnFrequency(s.cycle_frequency || d.cycle_policy?.cycle_frequency); view().innerHTML = `<section class="dashboard-status"><div class="dashboard-status-main"><p class="eyebrow">TASK BOARD</p><h2>任务清单</h2><p class="dashboard-time">${formatDashboardTime()}</p></div><div class="dashboard-status-side"><span>经营单元</span><strong>${unitName}</strong><small>${cycleLabel}循环 · ${pendingCount} 项待确认</small></div></section><section class="kpi-grid dashboard-metrics">${cards.map((item) => card(item.title, `<strong>${item.value}</strong><span class="card-desc">${item.desc || ""}</span>`, "metric-card")).join("")}</section><section class="page-section dashboard-queue"><div class="section-header"><h3>处理顺序</h3><span class="status-badge">实时任务</span></div>${renderTaskQueue(tasks)}</section>`; }
function renderOperatingUnit() { const payload = { name: "家居生活店铺组", subtitle: "淘宝 / 拼多多 / 抖音小店 · 4 家店铺 · 每天同步", dataMode: "Mock 数据", nextSystem: "聚水潭待接入", metrics: [ ["平台数量", "3", "淘宝 / 拼多多 / 抖音"], ["店铺数量", "4", "统一归入店铺组"], ["已接入数据", "4 类", "商品 / 库存 / 订单 / 售后"], ["待接入系统", "2", "聚水潭 / 广告后台"] ], shops: [ ["淘宝", "家居生活主店", "已连接", "商品 / 订单 / 库存"], ["拼多多", "家居百货店", "已连接", "商品 / 售后"], ["拼多多", "家清收纳店", "已连接", "商品 / 订单"], ["抖音小店", "家居好物号", "待授权", "暂未同步"] ], dataSources: [ ["ERP", "已接入 Mock", "商品、库存、成本"], ["CRM", "已接入 Mock", "客户、售后、退款"], ["聚水潭", "待接入", "多平台店铺数据汇总"], ["广告后台", "待接入", "ROI、投放、转化"] ] }; view().innerHTML = `<section class="unit-hero"><div><p class="eyebrow">STORE GROUP</p><h2>${payload.name}</h2><p>${payload.subtitle}</p></div><div class="unit-hero-side"><span>数据源</span><strong>${payload.dataMode}</strong><small>${payload.nextSystem}</small></div></section><section class="kpi-grid unit-metrics">${payload.metrics.map(([label, value, desc]) => `<article class="card unit-metric-card"><h3>${label}</h3><strong>${value}</strong><span class="card-desc">${desc}</span></article>`).join("")}</section><section class="page-section unit-store-section"><div class="section-header"><h3>关联店铺</h3><span class="status-badge">店铺群</span></div><div class="unit-store-table">${payload.shops.map(([platform, name, status, data]) => `<article class="unit-store-row"><strong>${platform}</strong><span>${name}</span><em>${status}</em><small>${data}</small></article>`).join("")}</div></section><section class="page-section unit-store-section"><div class="section-header"><h3>数据接入状态</h3><span class="status-badge pending">可扩展</span></div><div class="unit-store-table">${payload.dataSources.map(([system, status, usage]) => `<article class="unit-store-row"><strong>${system}</strong><span>${status}</span><em>${usage}</em><small>经营单元数据来源</small></article>`).join("")}</div></section>`; }
function renderReportManager() { $("pageTitle").textContent = reportManagerPayload.title; view().innerHTML = `<section class="report-hero"><div><p class="eyebrow">REPORT CENTER</p><h2>${reportManagerPayload.title}</h2><p>${reportManagerPayload.subtitle}</p></div><div class="report-hero-side"><span>数据来源</span><strong>ERP / CRM</strong><small>聚水潭待接入</small></div></section><section class="kpi-grid report-metrics">${reportManagerPayload.metrics.map((item) => `<article class="card report-metric-card"><h3>${item.label}</h3><strong>${item.value}</strong><span class="card-desc">${item.desc}</span></article>`).join("")}</section>${reportManagerPayload.groups.map((group) => `<section class="page-section report-section"><div class="section-header"><h3>${group.title}</h3><span class="status-badge">可查看</span></div><div class="report-card-list">${group.reports.map((report) => `<article class="report-card"><div><h3>${report.name}</h3><p>${report.desc}</p><div class="report-meta"><span>${report.source}</span><span>${report.status}</span><span>${report.count}</span></div></div><button type="button" onclick="renderReportDetail('${report.id}')">查看报表</button></article>`).join("")}</div></section>`).join("")}`; }
function renderReportDetail(reportId) { const report = reportManagerPayload.details[reportId]; if (!report) return; $("pageTitle").textContent = report.title; view().innerHTML = `<section class="report-detail-hero"><div><p class="eyebrow">${report.source} REPORT</p><h2>${report.title}</h2><p>从报表明细进入真实经营判断，避免只看系统状态。</p></div><div class="report-actions"><button type="button" onclick="renderReportManager()">返回报表管理</button><button type="button">重新同步</button><button type="button">导出报表</button></div></section><section class="kpi-grid report-metrics">${report.summary.map(([label, value]) => `<article class="card report-metric-card"><h3>${label}</h3><strong>${value}</strong></article>`).join("")}</section><section class="page-section report-table-section"><div class="section-header"><h3>报表明细</h3><span class="status-badge">Mock 数据</span></div><div class="report-table-wrap"><table class="report-table"><thead><tr>${report.columns.map((col) => `<th>${col}</th>`).join("")}</tr></thead><tbody>${report.rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section>`; }
async function renderProducts() { const d = raw(); const fallback = { items: safeArray(d.product_diagnosis) }; const payload = state.productsView || await fetchProductView("/api/business/products", fallback); state.productsView = payload; const rows = safeArray(payload.items).map((item) => `<div class="result-card"><h3>${item.product_name} ${badge(item.risk_level)}</h3>${kv([["库存", item.stock ?? "-"], ["毛利", item.gross_margin ?? "-"], ["活动毛利", item.activity_margin ?? "-"]])}${list(item.suggestions || item.suggested_actions || [])}</div>`).join(""); view().innerHTML = `<section class="result-list">${rows || card("暂无商品体检", "<p>当前没有可展示的商品结果。</p>")}</section>`; }
async function renderCompetitors() { const d = raw(); const c = d.competitor_analysis || {}; const fallback = { competitor_count: c.competitor_count, trigger_product: c.reference_product, price_gap: c.price_gap, bad_review_keywords: c.review_gap?.top_bad_review_keywords, opportunity_actions: c.review_gap?.opportunity_actions, next_action: c.next_action }; const payload = state.competitorsView || await fetchProductView("/api/business/competitors", fallback); state.competitorsView = payload; view().innerHTML = `<section class="page-section">${kv([["触发商品", payload.trigger_product?.product_name || "-"], ["参考对象", payload.competitor_count || 0], ["价格", payload.price_gap?.position || "-"], ["动作", payload.next_action || "-"]])}</section><section class="two-column">${card("差评", list(payload.bad_review_keywords || []))}${card("机会", list(payload.opportunity_actions || []))}</section>`; }
async function renderListing() { const d = raw(); const plan = d.listing_growth_plan || {}; const draft = plan.listing_draft || {}; const fallback = { top_candidate: plan.top_candidate || {}, title_draft: draft.title_draft, image_plan: draft.image_plan || [], sku_plan: draft.sku_plan || [], compliance_checklist: draft.compliance_checklist || [] }; const payload = state.listingView || await fetchProductView("/api/business/listing", fallback); state.listingView = payload; const top = payload.top_candidate || {}; view().innerHTML = `<section class="page-section">${kv([["候选", top.product_name || "-"], ["评分", top.score || "-"], ["毛利", top.expected_margin ?? "-"], ["毛利率", top.margin_rate ?? "-"]])}</section><section class="two-column">${card("标题", `<div class="title-draft">${payload.title_draft || "-"}</div>`)}${card("检查", list(payload.compliance_checklist || []))}</section><section class="two-column">${card("主图", list(payload.image_plan || []))}${card("规格", list(payload.sku_plan || []))}</section>`; }
async function renderTraffic() { const d = raw(); const report = d.traffic_feedback_report || {}; const fallback = { experiment_count: report.experiment_count, next_action: report.next_action, loopback_actions: report.loopback_actions, items: safeArray(report.diagnoses) }; const payload = state.trafficView || await fetchProductView("/api/business/traffic", fallback); state.trafficView = payload; const rows = safeArray(payload.items).map((item) => `<div class="task-row"><strong>${item.product_id || item.experiment_id}</strong><span>${item.traffic_source || "-"}</span>${badge(item.risk_level)}<small>${item.decision_label || cnDecision(item.decision)}</small></div>`).join(""); view().innerHTML = `<section class="page-section">${kv([["测试", payload.experiment_count || 0], ["结论", payload.next_action || "-"], ["回流", safeArray(payload.loopback_actions).join(" / ") || "-"], ["状态", "待确认"]])}</section><section class="task-table">${rows}</section>`; }
async function renderApprovals() { let actions = []; if (state.apiMode) { try { actions = (await fetchJson("/api/business/actions")).items || []; } catch { actions = []; } } const d = raw(); const tasks = actions.length ? actions : safeArray(d.approval_required_tasks?.length ? d.approval_required_tasks : d.rpa_tasks).map((task) => ({ action_id: task.task_id, action_name: task.task_type, risk_level: task.risk_level, suggestion: task.ai_suggestion })); const rows = tasks.map((task) => `<div class="result-card"><h3>${task.action_name || "动作"} ${badge(task.risk_level)}</h3><div class="action-line">${task.suggestion || "待确认"}</div><div class="task-actions"><button onclick="updateTask('${task.action_id}', 'approve')">确认</button><button class="secondary" onclick="updateTask('${task.action_id}', 'reject')">拒绝</button></div></div>`).join(""); view().innerHTML = `<section class="result-list">${rows}</section>`; }
async function renderReports() { if (state.apiMode && !state.reportText) { try { state.reportText = await (await fetch("/api/business/report")).text(); } catch { state.reportText = "暂无报告"; } } const summary = raw().summary || {}; view().innerHTML = `<section class="page-section">${kv([["经营单元", summary.unit_name || "-"], ["频率", cnFrequency(summary.cycle_frequency)], ["重点", cnModule(summary.loop_next_module)], ["确认", summary.approval_required_count || 0]])}</section><section class="page-section"><div class="report-preview"><pre>${state.reportText || "暂无报告"}</pre></div></section>`; }
async function updateTask(taskId, action) { if (!state.apiMode) return; const response = await fetch(`/api/approvals/${taskId}/${action}`, { method: "POST" }); if (!response.ok) return; await refreshWorkflow(); await renderApprovals(); }
async function refreshAndRender() { await refreshWorkflow(); await renderRoute(); }
async function refreshCurrentView() { await renderRoute(); }
window.renderReportDetail = renderReportDetail;
window.renderReportManager = renderReportManager;
window.updateTask = updateTask;
window.refreshCurrentView = refreshCurrentView;
window.refreshAndRender = refreshAndRender;
$("refreshBtn").addEventListener("click", refreshAndRender);
window.addEventListener("hashchange", renderRoute);
refreshAndRender();
