const fallbackData = {
  summary: { product_count: 3, customer_count: 4, rpa_task_count: 7, approval_required_count: 7, auto_execution_allowed_count: 0 },
  product_diagnosis: [
    { product_id: "P001", product_name: "遮阳伞", risk_level: "medium", risks: ["库存高", "活动价风险"], suggested_actions: ["生成 SKU 价格建议表", "活动报名前人工确认"], gross_margin: 8.2, activity_margin: 1.2, stock: 200 },
    { product_id: "P003", product_name: "护腰坐垫", risk_level: "high", risks: ["敏感类目", "退款异常"], suggested_actions: ["进入售后归因工作流", "先做合规检查"], gross_margin: 11.5, activity_margin: 5.5, stock: 80 },
  ],
  customer_segmentation: [
    { customer_id: "C001", segment: "高价值客户", risk_level: "low", tags: ["高价值", "复购潜力"], recommended_actions: ["生成老客复购任务草案"] },
    { customer_id: "C004", segment: "售后敏感客户", risk_level: "high", tags: ["售后敏感", "流失风险"], recommended_actions: ["优先生成售后归因表", "不直接营销触达"] },
  ],
  rpa_tasks: [
    { task_id: "TASK_PRODUCT_DAILY_001", task_type: "daily_report", risk_level: "low", approval_status: "pending", auto_execution_allowed: false, ai_suggestion: "生成商品经营日报和下一轮复盘摘要。" },
    { task_id: "TASK_SKU_PRICE_001", task_type: "sku_price_table", risk_level: "medium", approval_status: "pending", auto_execution_allowed: false, ai_suggestion: "生成 SKU 价格建议表，标记保本线、活动价风险和人工确认项。" },
    { task_id: "TASK_CRM_AFTER_SALES_004", task_type: "after_sales_analysis", risk_level: "high", approval_status: "pending", auto_execution_allowed: false, ai_suggestion: "生成售后归因表，不自动营销触达。" },
  ],
  approval_required_tasks: [],
  rag_context: {
    activity_price: [{ source: "platform_rules.md", snippet: "活动价需要结合成本、物流、退款损耗判断，不建议低于保本线参与活动。" }],
    after_sales: [{ source: "customer_service_sop.md", snippet: "售后问题应先判断商品质量、详情页误导、规格说明不清、物流问题、客服响应问题。" }],
    customer_touch: [{ source: "compliance_rules.md", snippet: "客户触达必须谨慎，不自动群发，不骚扰用户，不泄露隐私信息。" }],
  },
};
fallbackData.approval_required_tasks = fallbackData.rpa_tasks;

const fallbackImportStatus = {
  status: "local_preview",
  datasets: ["products", "orders", "inventory", "refunds", "customers", "customer_tags", "interactions"].map((name) => ({ dataset_name: name, label: name, filename: `mock_${name}.csv`, row_count: 0, status: "preview" })),
  relationship_checks: [],
};

const fallbackDbStatus = {
  ok: false,
  database: { type: "sqlite", path: "logs/product_workbench.sqlite3", exists: false, size_bytes: 0 },
  tables: ["workflow_runs", "execution_logs", "import_records", "approval_records", "task_status", "report_records"].map((table_name) => ({ table_name, record_count: 0, latest_at: null })),
  summary: { table_count: 6, total_records: 0, latest_at: null },
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
  workflowRuns: [],
  executionLogs: [],
  selectedWorkflowRunId: null,
  selectedRunLogs: [],
  dbStatus: null,
  logFilters: { workflow_type: "", status: "", limit: 20, offset: 0 },
  totals: { runs: 0, logs: 0, selected: 0 },
};

const routes = {
  dashboard: ["经营总览", "查看商品、客户、任务、审批和安全边界的整体状态。", renderDashboard],
  "data-import": ["数据导入", "Mock CSV 校验、导入记录和字段关系检查。", renderDataImport],
  diagnosis: ["AI 诊断", "商品诊断、客户分层、售后归因与 RAG 依据。", renderDiagnosis],
  tasks: ["任务中心", "从 SQLite task_status 读取任务审批状态，并合并当前任务草案。", renderTasks],
  approvals: ["审批中心", "确认 / 拒绝中高风险任务，并查看 ApprovalRecord 历史。", renderApprovals],
  reports: ["报告中心", "展示 ReportRecord 列表和 Markdown 报告内容。", renderReports],
  knowledge: ["知识库", "平台规则、合规风控、运营方法和客服 SOP 的 RAG 依据。", renderKnowledge],
  logs: ["运行日志", "支持分页、筛选和按 workflow_run_id 查看节点详情。", renderLogs],
  system: ["系统状态", "检查 SQLite 文件、数据表、记录数和最近更新时间。", renderSystem],
};

const $ = (id) => document.getElementById(id);
const view = () => $("appView");
const data = () => state.apiData || fallbackData;
const qs = (params) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== null && value !== "") search.set(key, value); });
  return search.toString();
};
const badge = (level) => `<span class="badge ${level || "low"}">${level === "high" ? "高风险" : level === "medium" ? "中风险" : "低风险"}</span>`;
const statusBadge = (status) => `<span class="status-badge ${status || "preview"}">${({ success: "成功", failed: "失败", running: "运行中", approved: "已确认", rejected: "已拒绝", pending: "待确认", preview: "预览", passed: "通过", warning: "警告", markdown: "Markdown" }[status]) || status || "预览"}</span>`;
const card = (title, body) => `<article class="card"><h3>${title}</h3>${body}</article>`;
const list = (items) => `<ul class="clean-list">${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

async function refreshWorkflow() {
  try {
    state.apiData = await fetchJson("/api/demo/run");
    state.apiMode = true;
    $("apiModeBadge").textContent = "API 模式";
    $("apiModeBadge").className = "mode-badge api";
  } catch (error) {
    state.apiData = fallbackData;
    state.apiMode = false;
    $("apiModeBadge").textContent = "本地样例模式";
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
  const summary = d.summary || {};
  view().innerHTML = `<section class="kpi-grid">
    ${card("商品诊断", `<strong>${summary.product_count || d.product_diagnosis.length}</strong><p>当前诊断商品数</p>`)}
    ${card("客户分层", `<strong>${summary.customer_count || d.customer_segmentation.length}</strong><p>当前客户分层数</p>`)}
    ${card("任务草案", `<strong>${summary.rpa_task_count || d.rpa_tasks.length}</strong><p>自动执行：${summary.auto_execution_allowed_count || 0}</p>`)}
    ${card("待确认", `<strong>${summary.approval_required_count || d.approval_required_tasks.length}</strong><p>高风险默认人工确认</p>`)}
  </section><section class="two-column">${card("产品主线", list(["导入经营数据", "AI / RAG 经营诊断", "生成任务草案", "人工确认", "报告输出与日志回写"]))}${card("当前边界", list(["不接真实店铺后台", "不自动改价", "不自动群发客户", "不自动退款"]))}</section>`;
}

async function renderDataImport() {
  if (state.apiMode) {
    try { state.importValidation = await fetchJson("/api/data/validate", { method: "POST" }); state.importRecords = await fetchJson("/api/data/imports"); } catch { state.importValidation = fallbackImportStatus; state.importRecords = []; }
  } else { state.importValidation = fallbackImportStatus; state.importRecords = []; }
  const validation = state.importValidation || fallbackImportStatus;
  const datasetRows = (validation.datasets || []).map((item) => `<div><strong>${item.label || item.dataset_name}</strong><span>${item.filename || "-"}</span><span>${item.row_count ?? 0} 行</span>${statusBadge(item.status)}</div>`).join("");
  const recordRows = state.importRecords.length ? state.importRecords.map((item) => `<div><strong>${item.import_id}</strong><span>${item.created_at}</span><span>${item.total_rows} 行</span>${statusBadge(item.status)}</div>`).join("") : `<div><strong>暂无导入记录</strong><span>点击确认导入后生成。</span><span>-</span>${statusBadge("preview")}</div>`;
  view().innerHTML = `<section class="page-section"><div class="section-header"><div><h2>数据导入校验</h2><p class="muted">状态：${validation.status}</p></div><div class="button-group"><button onclick="refreshCurrentView()">重新校验</button><button onclick="importMockData()">确认导入 Mock 数据</button></div></div><div class="table-like import-table">${datasetRows}</div></section><section class="page-section"><h2>导入记录</h2><div class="table-like import-table records-table">${recordRows}</div></section>`;
}

function renderDiagnosis() {
  const d = data();
  const productCards = d.product_diagnosis.map((item) => `<div class="result-card"><h3>${item.product_id} - ${item.product_name} ${badge(item.risk_level)}</h3><p>风险：${(item.risks || []).join("，")}</p><p>建议：${(item.suggested_actions || []).join("；")}</p></div>`).join("");
  const customerCards = d.customer_segmentation.map((item) => `<div class="result-card"><h3>${item.customer_id} - ${item.segment} ${badge(item.risk_level)}</h3><p>标签：${(item.tags || []).join("，")}</p><p>建议：${(item.recommended_actions || []).join("；")}</p></div>`).join("");
  view().innerHTML = `<section class="page-section"><h2>商品诊断</h2><div class="result-list">${productCards}</div></section><section class="page-section"><h2>客户分层</h2><div class="result-list">${customerCards}</div></section>`;
}

async function renderTasks() {
  try { state.tasks = state.apiMode ? await fetchJson("/api/tasks") : data().rpa_tasks; } catch { state.tasks = data().rpa_tasks; }
  const rows = state.tasks.map((task) => `<div class="task-row"><div><strong>${task.task_id}</strong><p>${task.ai_suggestion || task.task_type}</p></div><span>${task.task_type}</span>${badge(task.risk_level)}${statusBadge(task.approval_status || task.status || "pending")}<small>自动执行：${task.auto_execution_allowed}</small></div>`).join("");
  view().innerHTML = `<section class="page-section"><div class="section-header"><div><h2>任务状态</h2><p class="muted">读取 SQLite task_status 并合并当前任务草案。</p></div><button onclick="refreshCurrentView()">刷新任务状态</button></div><div class="task-table">${rows}</div></section>`;
}

async function renderApprovals() {
  const d = data();
  try { state.approvalRecords = state.apiMode ? await fetchJson("/api/approvals/records") : []; } catch { state.approvalRecords = []; }
  const cards = (d.approval_required_tasks || d.rpa_tasks).map((task) => `<div class="result-card"><h3>${task.task_id} ${badge(task.risk_level)}</h3><p>${task.ai_suggestion || task.task_type}</p><div class="task-actions"><button onclick="updateTask('${task.task_id}', 'approve')">确认</button><button class="secondary" onclick="updateTask('${task.task_id}', 'reject')">拒绝</button></div></div>`).join("");
  const rows = state.approvalRecords.length ? state.approvalRecords.map((record) => `<div><strong>${record.task_id}</strong><span>${record.operator || "demo_user"}</span><span>${record.created_at || record.updated_at || "-"}</span>${statusBadge(record.approval_status)}</div>`).join("") : `<div><strong>暂无审批历史</strong><span>确认或拒绝任务后生成。</span><span>-</span>${statusBadge("preview")}</div>`;
  view().innerHTML = `<section class="page-section"><h2>待人工确认</h2><div class="result-list">${cards}</div></section><section class="page-section"><h2>审批历史</h2><div class="table-like import-table records-table">${rows}</div></section>`;
}

async function renderReports() {
  try { const payload = state.apiMode ? await fetchJson("/api/reports") : { reports: [] }; state.reportRecords = payload.reports || []; } catch { state.reportRecords = []; }
  if (state.apiMode && !state.reportText) { try { state.reportText = await (await fetch("/api/reports/demo")).text(); } catch { state.reportText = "API 报告读取失败。"; } }
  const rows = state.reportRecords.length ? state.reportRecords.map((record) => `<div><strong>${record.report_id}</strong><span>${record.report_type}</span><span>${record.path || "-"}</span>${statusBadge(record.format || "markdown")}</div>`).join("") : `<div><strong>暂无报告记录</strong><span>运行完整工作流后生成。</span><span>-</span>${statusBadge("preview")}</div>`;
  view().innerHTML = `<section class="page-section"><h2>ReportRecord</h2><div class="table-like import-table records-table">${rows}</div></section><section class="page-section"><h2>报告内容预览</h2><div class="report-preview"><pre>${state.reportText || "运行 API 后可查看 Markdown 报告。"}</pre></div></section>`;
}

function renderKnowledge() {
  const items = Object.entries(data().rag_context || {}).map(([key, values]) => { const first = values?.[0] || {}; return `<div class="result-card"><h3>${key}</h3><p>${first.snippet || "已召回相关知识片段"}</p><small>来源：${first.source || "knowledge_base"}</small></div>`; }).join("");
  view().innerHTML = `<section class="page-section"><h2>RAG 依据</h2><div class="result-list">${items}</div></section>`;
}

async function renderLogs() {
  const params = qs(state.logFilters);
  try {
    const runPayload = state.apiMode ? await fetchJson(`/api/logs/workflow-runs?${params}`) : { items: [], total: 0 };
    const logPayload = state.apiMode ? await fetchJson(`/api/logs/execution-logs?${qs({ limit: state.logFilters.limit, offset: state.logFilters.offset, status: state.logFilters.status })}`) : { items: [], total: 0 };
    state.workflowRuns = runPayload.items || [];
    state.executionLogs = logPayload.items || [];
    state.totals.runs = runPayload.total || 0;
    state.totals.logs = logPayload.total || 0;
  } catch { state.workflowRuns = []; state.executionLogs = []; state.totals.runs = 0; state.totals.logs = 0; }
  const filters = `<div class="filter-bar"><label>类型 <select onchange="updateLogFilter('workflow_type', this.value)"><option value="">全部</option><option value="full_mock_workflow" ${state.logFilters.workflow_type === "full_mock_workflow" ? "selected" : ""}>完整诊断</option><option value="data_import_mock_csv" ${state.logFilters.workflow_type === "data_import_mock_csv" ? "selected" : ""}>数据导入</option><option value="task_approval" ${state.logFilters.workflow_type === "task_approval" ? "selected" : ""}>任务审批</option></select></label><label>状态 <select onchange="updateLogFilter('status', this.value)"><option value="">全部</option><option value="success" ${state.logFilters.status === "success" ? "selected" : ""}>成功</option><option value="failed" ${state.logFilters.status === "failed" ? "selected" : ""}>失败</option><option value="running" ${state.logFilters.status === "running" ? "selected" : ""}>运行中</option></select></label><label>条数 <select onchange="updateLogFilter('limit', this.value)"><option value="10" ${Number(state.logFilters.limit) === 10 ? "selected" : ""}>10</option><option value="20" ${Number(state.logFilters.limit) === 20 ? "selected" : ""}>20</option><option value="50" ${Number(state.logFilters.limit) === 50 ? "selected" : ""}>50</option></select></label><button class="secondary" onclick="resetLogFilters()">重置筛选</button></div>`;
  const runRows = state.workflowRuns.length ? state.workflowRuns.map((run) => `<div><strong>${run.workflow_run_id}</strong><span>${run.workflow_type}</span><span>${run.finished_at || run.started_at || "-"}</span>${statusBadge(run.status)}<button class="secondary" onclick="selectWorkflowRun('${run.workflow_run_id}')">查看节点</button></div>`).join("") : `<div><strong>暂无 WorkflowRun</strong><span>运行后生成。</span><span>-</span>${statusBadge("preview")}</div>`;
  const selectedRows = state.selectedRunLogs.length ? state.selectedRunLogs.map((log) => `<div><strong>${log.node_name}</strong><span>${log.log_id}</span><span>${log.created_at}</span>${statusBadge(log.status)}</div>`).join("") : `<div><strong>未选择 WorkflowRun</strong><span>点击查看节点。</span><span>-</span>${statusBadge("preview")}</div>`;
  const logRows = state.executionLogs.length ? state.executionLogs.map((log) => `<div><strong>${log.node_name}</strong><span>${log.workflow_run_id}</span><span>${log.created_at}</span>${statusBadge(log.status)}</div>`).join("") : `<div><strong>暂无 ExecutionLog</strong><span>运行节点后生成。</span><span>-</span>${statusBadge("preview")}</div>`;
  view().innerHTML = `<section class="page-section"><div class="section-header"><div><h2>WorkflowRun</h2><p class="muted">共 ${state.totals.runs} 条，当前显示 ${state.workflowRuns.length} 条。</p></div><button onclick="renderLogs()">刷新日志</button></div>${filters}<div class="table-like import-table log-table">${runRows}</div></section><section class="page-section"><h2>当前选中运行 ${state.selectedWorkflowRunId || ""}</h2><div class="table-like import-table records-table">${selectedRows}</div></section><section class="page-section"><h2>最新 ExecutionLog</h2><p class="muted">共 ${state.totals.logs} 条。</p><div class="table-like import-table records-table">${logRows}</div></section>`;
}

async function renderSystem() {
  try { state.dbStatus = state.apiMode ? await fetchJson("/api/system/db-status") : fallbackDbStatus; } catch { state.dbStatus = fallbackDbStatus; }
  const status = state.dbStatus;
  const tableRows = (status.tables || []).map((item) => `<div><strong>${item.table_name}</strong><span>${item.record_count || 0} 条</span><span>${item.latest_at || "暂无"}</span>${statusBadge((item.record_count || 0) > 0 ? "success" : "preview")}</div>`).join("");
  view().innerHTML = `<section class="kpi-grid">${card("数据库", `<strong>${status.database.exists ? "已生成" : "未生成"}</strong><p>${status.database.path}</p>`)}${card("表数量", `<strong>${status.summary.table_count || 0}</strong><p>当前 SQLite 表</p>`)}${card("总记录数", `<strong>${status.summary.total_records || 0}</strong><p>所有持久化记录</p>`)}${card("文件大小", `<strong>${status.database.size_bytes || 0}</strong><p>bytes</p>`)}</section><section class="page-section"><div class="section-header"><div><h2>SQLite 表状态</h2><p class="muted">最近更新时间：${status.summary.latest_at || "暂无"}</p></div><div class="button-group"><button onclick="renderSystem()">刷新系统状态</button><button class="secondary" onclick="clearDemoData()">清空 Demo 数据</button></div></div><div class="table-like import-table records-table">${tableRows}</div></section><section class="two-column">${card("当前存储对象", list(["WorkflowRun", "ExecutionLog", "ImportRecord", "ApprovalRecord", "TaskStatus", "ReportRecord"]))}${card("清空范围", list(["删除生成的 SQLite 数据库", "删除 JSONL 审计日志", "不删除源码 / Mock 数据 / 产品文档", "清空后自动重建空表结构"]))}</section>`;
}

async function importMockData() {
  if (!state.apiMode) return alert("启动 FastAPI 后可生成导入记录。");
  await fetchJson("/api/data/import/mock", { method: "POST" });
  await renderDataImport();
}
async function updateTask(taskId, action) {
  if (!state.apiMode) return alert("启动 FastAPI 后可记录确认 / 拒绝状态。");
  const response = await fetch(`/api/approvals/${taskId}/${action}`, { method: "POST" });
  if (!response.ok) return alert("任务状态更新失败");
  await refreshWorkflow();
  await renderApprovals();
}
async function updateLogFilter(field, value) {
  state.logFilters[field] = field === "limit" ? Number(value) : value;
  state.logFilters.offset = 0;
  await renderLogs();
}
async function resetLogFilters() {
  state.logFilters = { workflow_type: "", status: "", limit: 20, offset: 0 };
  state.selectedWorkflowRunId = null;
  state.selectedRunLogs = [];
  await renderLogs();
}
async function selectWorkflowRun(id) {
  state.selectedWorkflowRunId = id;
  try {
    const payload = await fetchJson(`/api/logs/workflow-runs/${id}/execution-logs?${qs({ limit: 100, status: state.logFilters.status })}`);
    state.selectedRunLogs = payload.items || [];
  } catch { state.selectedRunLogs = []; }
  await renderLogs();
}
async function clearDemoData() {
  if (!state.apiMode) return alert("启动 FastAPI 后才能清空运行数据。");
  if (!confirm("确认清空 Demo 运行数据？不会删除源码、Mock 数据和产品文档。")) return;
  const response = await fetch("/api/system/clear-demo-data?confirm=true&include_audit_logs=true", { method: "POST" });
  if (!response.ok) return alert("清空失败，请检查 API 日志。");
  state.reportText = "";
  state.reportRecords = [];
  state.workflowRuns = [];
  state.executionLogs = [];
  state.selectedRunLogs = [];
  state.selectedWorkflowRunId = null;
  await renderSystem();
}
async function refreshCurrentView() { await renderRoute(); }
async function refreshAndRender() { await refreshWorkflow(); await renderRoute(); }

window.importMockData = importMockData;
window.updateTask = updateTask;
window.updateLogFilter = updateLogFilter;
window.resetLogFilters = resetLogFilters;
window.selectWorkflowRun = selectWorkflowRun;
window.clearDemoData = clearDemoData;
window.refreshCurrentView = refreshCurrentView;
window.refreshAndRender = refreshAndRender;

$("refreshBtn").addEventListener("click", refreshAndRender);
window.addEventListener("hashchange", renderRoute);
refreshAndRender();
