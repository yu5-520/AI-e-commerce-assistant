const fallbackData = {
  summary: {
    product_count: 3,
    customer_count: 4,
    rpa_task_count: 7,
    approval_required_count: 7,
    auto_execution_allowed_count: 0,
  },
  product_diagnosis: [
    {
      product_id: "P001",
      product_name: "遮阳伞",
      risk_level: "medium",
      risks: ["high_inventory_low_order_risk", "activity_price_margin_risk"],
      suggested_actions: ["生成 SKU 价格建议表", "活动报名前人工确认"],
      gross_margin: 8.2,
      activity_margin: 1.2,
      stock: 200,
      refund_count: 0,
    },
    {
      product_id: "P003",
      product_name: "护腰坐垫",
      risk_level: "high",
      risks: ["sensitive_category_compliance_risk", "refund_abnormal_risk"],
      suggested_actions: ["进入售后归因工作流", "先做合规检查"],
      gross_margin: 11.5,
      activity_margin: 5.5,
      stock: 80,
      refund_count: 2,
    },
  ],
  customer_segmentation: [
    {
      customer_id: "C001",
      segment: "高价值客户",
      risk_level: "low",
      tags: ["高价值", "复购潜力"],
      recommended_actions: ["生成老客复购任务草案"],
    },
    {
      customer_id: "C004",
      segment: "售后敏感客户",
      risk_level: "high",
      tags: ["售后敏感", "流失风险"],
      recommended_actions: ["优先生成售后归因表", "不直接营销触达"],
    },
  ],
  rpa_tasks: [
    {
      task_id: "TASK_PRODUCT_DAILY_001",
      task_type: "daily_report",
      risk_level: "low",
      approval_status: "pending",
      auto_execution_allowed: false,
      ai_suggestion: "生成商品经营日报和下一轮复盘摘要。",
    },
    {
      task_id: "TASK_SKU_PRICE_001",
      task_type: "sku_price_table",
      risk_level: "medium",
      approval_status: "pending",
      auto_execution_allowed: false,
      ai_suggestion: "生成 SKU 价格建议表，标记保本线、活动价风险和人工确认项。",
    },
    {
      task_id: "TASK_CRM_AFTER_SALES_004",
      task_type: "after_sales_analysis",
      risk_level: "high",
      approval_status: "pending",
      auto_execution_allowed: false,
      ai_suggestion: "生成售后归因表，不自动营销触达。",
    },
  ],
  approval_required_tasks: [],
  rag_context: {
    activity_price: [{ source: "platform_rules.md", snippet: "活动价需要结合成本、物流、退款损耗判断，不建议低于保本线参与活动。" }],
    after_sales: [{ source: "customer_service_sop.md", snippet: "售后问题应先判断商品质量、详情页误导、规格说明不清、物流问题、客服响应问题。" }],
    customer_touch: [{ source: "compliance_rules.md", snippet: "客户触达必须谨慎，不自动群发，不骚扰用户，不泄露隐私信息。" }],
  },
};

const fallbackImportStatus = {
  status: "local_preview",
  datasets: [
    { dataset_name: "products", label: "商品表", filename: "mock_products.csv", row_count: 3, status: "preview" },
    { dataset_name: "orders", label: "订单表", filename: "mock_orders.csv", row_count: 4, status: "preview" },
    { dataset_name: "inventory", label: "库存表", filename: "mock_inventory.csv", row_count: 3, status: "preview" },
    { dataset_name: "refunds", label: "退款表", filename: "mock_refunds.csv", row_count: 2, status: "preview" },
    { dataset_name: "customers", label: "客户表", filename: "mock_customers.csv", row_count: 4, status: "preview" },
    { dataset_name: "customer_tags", label: "客户标签表", filename: "mock_customer_tags.csv", row_count: 6, status: "preview" },
    { dataset_name: "interactions", label: "客户互动表", filename: "mock_interactions.csv", row_count: 4, status: "preview" },
  ],
  relationship_checks: [],
};

fallbackData.approval_required_tasks = fallbackData.rpa_tasks.filter((task) => task.requires_approval !== false);

const routes = {
  dashboard: {
    title: "经营总览",
    subtitle: "查看商品、客户、任务、审批和安全边界的整体状态。",
    render: renderDashboard,
  },
  "data-import": {
    title: "数据导入",
    subtitle: "MVP 阶段先跑通 Mock CSV 校验、导入记录和字段关系检查。",
    render: renderDataImport,
  },
  diagnosis: {
    title: "AI 诊断",
    subtitle: "商品诊断、客户分层、售后归因与 RAG 依据。",
    render: renderDiagnosis,
  },
  tasks: {
    title: "任务中心",
    subtitle: "将 AI 建议转成可确认、可追溯的 RPA 任务草案。",
    render: renderTasks,
  },
  approvals: {
    title: "审批中心",
    subtitle: "确认或拒绝中高风险任务，避免 AI / RPA 越权执行。",
    render: renderApprovals,
  },
  reports: {
    title: "报告中心",
    subtitle: "输出商品诊断、客户分层、售后归因和复盘报告。",
    render: renderReports,
  },
  knowledge: {
    title: "知识库",
    subtitle: "平台规则、合规风控、运营方法和客服 SOP 的 RAG 依据。",
    render: renderKnowledge,
  },
};

const state = {
  apiData: null,
  apiMode: false,
  reportText: "",
  importValidation: null,
  importRecords: [],
};

function view() {
  return document.getElementById("appView");
}

function getData() {
  return state.apiData || fallbackData;
}

function badge(level) {
  const label = level === "high" ? "高风险" : level === "medium" ? "中风险" : "低风险";
  return `<span class="badge ${level || "low"}">${label}</span>`;
}

function statusBadge(status) {
  return `<span class="status-badge ${status || "pending"}">${status || "pending"}</span>`;
}

function importStatusBadge(status) {
  const labelMap = { passed: "通过", failed: "失败", warning: "警告", preview: "预览", local_preview: "本地预览" };
  return `<span class="status-badge ${status || "preview"}">${labelMap[status] || status || "预览"}</span>`;
}

function card(title, body, extraClass = "") {
  return `<article class="card ${extraClass}"><h3>${title}</h3>${body}</article>`;
}

function list(items) {
  if (!items || !items.length) return "<p class='muted'>暂无数据。</p>";
  return `<ul class="clean-list">${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

async function refreshWorkflow() {
  try {
    state.apiData = await fetchJson("/api/demo/run");
    state.apiMode = true;
    document.getElementById("apiModeBadge").textContent = "API 模式";
    document.getElementById("apiModeBadge").className = "mode-badge api";
  } catch (error) {
    state.apiData = fallbackData;
    state.apiMode = false;
    document.getElementById("apiModeBadge").textContent = "本地样例模式";
    document.getElementById("apiModeBadge").className = "mode-badge local";
  }
}

async function refreshImportStatus(createRecord = false) {
  if (!state.apiMode) {
    state.importValidation = fallbackImportStatus;
    state.importRecords = [];
    return;
  }

  try {
    if (createRecord) {
      const importRecord = await fetchJson("/api/data/import/mock", { method: "POST" });
      state.importValidation = importRecord.validation;
    } else {
      state.importValidation = await fetchJson("/api/data/validate", { method: "POST" });
    }
    state.importRecords = await fetchJson("/api/data/imports");
  } catch (error) {
    state.importValidation = fallbackImportStatus;
    state.importRecords = [];
  }
}

function currentRoute() {
  const route = window.location.hash.replace("#", "") || "dashboard";
  return routes[route] ? route : "dashboard";
}

function setActiveNav(route) {
  document.querySelectorAll(".nav a").forEach((link) => {
    link.classList.toggle("active", link.dataset.route === route);
  });
}

async function renderRoute() {
  const route = currentRoute();
  const config = routes[route];
  setActiveNav(route);
  document.getElementById("pageTitle").textContent = config.title;
  document.getElementById("pageSubtitle").textContent = config.subtitle;
  await config.render(getData());
}

function renderDashboard(data) {
  const summary = data.summary || {};
  const highRiskProducts = data.product_diagnosis.filter((item) => item.risk_level === "high").length;
  const highRiskCustomers = data.customer_segmentation.filter((item) => item.risk_level === "high").length;

  view().innerHTML = `
    <section class="kpi-grid">
      ${card("商品诊断", `<strong>${summary.product_count || data.product_diagnosis.length}</strong><p>高风险商品：${highRiskProducts}</p>`)}
      ${card("客户分层", `<strong>${summary.customer_count || data.customer_segmentation.length}</strong><p>高风险客户：${highRiskCustomers}</p>`)}
      ${card("任务草案", `<strong>${summary.rpa_task_count || data.rpa_tasks.length}</strong><p>自动执行：${summary.auto_execution_allowed_count || 0}</p>`)}
      ${card("待人工确认", `<strong>${summary.approval_required_count || data.approval_required_tasks.length}</strong><p>默认不执行高风险动作</p>`)}
    </section>
    <section class="two-column">
      ${card("产品主线", list(["导入经营数据", "AI / RAG 经营诊断", "生成任务草案", "人工确认", "报告输出与日志回写"]))}
      ${card("当前边界", list(["不接真实店铺后台", "不自动改价 / 投放 / 报名活动", "不自动群发客户", "不自动处理退款", "CRM 只使用脱敏 Mock 数据"]))}
    </section>
  `;
}

async function renderDataImport() {
  await refreshImportStatus(false);
  const validation = state.importValidation || fallbackImportStatus;
  const datasets = validation.datasets || [];
  const relationshipChecks = validation.relationship_checks || [];
  const records = state.importRecords || [];

  const datasetRows = datasets.map((item) => `
    <div>
      <strong>${item.label || item.dataset_name}</strong>
      <span>${item.filename || "-"}</span>
      <span>${item.row_count ?? 0} 行</span>
      ${importStatusBadge(item.status)}
    </div>
  `).join("");

  const relationRows = relationshipChecks.length
    ? relationshipChecks.map((item) => `
      <div>
        <strong>${item.check_name}</strong>
        <span>缺失 ID：${(item.missing_ids || []).join("，") || "无"}</span>
        ${importStatusBadge(item.status)}
      </div>
    `).join("")
    : `<div><strong>关系校验</strong><span>本地样例模式下仅展示预览；启动 API 后执行真实校验。</span>${importStatusBadge("preview")}</div>`;

  const recordRows = records.length
    ? records.map((item) => `
      <div>
        <strong>${item.import_id}</strong>
        <span>${item.created_at}</span>
        <span>${item.total_rows} 行</span>
        ${importStatusBadge(item.status)}
      </div>
    `).join("")
    : `<div><strong>暂无导入记录</strong><span>点击“确认导入 Mock 数据”后生成记录。</span>${importStatusBadge("preview")}</div>`;

  view().innerHTML = `
    <section class="page-section">
      <div class="section-header">
        <div>
          <h2>数据导入校验</h2>
          <p class="muted">状态：${validation.status || "local_preview"}｜失败：${validation.failed_count || 0}｜警告：${validation.warning_count || 0}</p>
        </div>
        <div class="button-group">
          <button onclick="validateImportAndRender()">重新校验</button>
          <button onclick="importMockAndRender()">确认导入 Mock 数据</button>
        </div>
      </div>
      <div class="table-like import-table">${datasetRows}</div>
    </section>
    <section class="page-section">
      <h2>关系校验</h2>
      <div class="table-like import-table relation-table">${relationRows}</div>
    </section>
    <section class="page-section">
      <h2>导入记录</h2>
      <div class="table-like import-table records-table">${recordRows}</div>
    </section>
    <section class="two-column">
      ${card("当前已校验", list(["必填字段", "数字字段", "product_id 关联", "order_id 关联", "customer_id 关联"]))}
      ${card("后续产品化", list(["CSV / Excel 上传", "字段映射确认", "错误行报告", "数据快照保存", "WorkflowRun 日志"] ))}
    </section>
  `;
}

function renderDiagnosis(data) {
  const productCards = data.product_diagnosis.map((item) => `
    <div class="result-card">
      <h3>${item.product_id} - ${item.product_name} ${badge(item.risk_level)}</h3>
      <p>风险标签：${(item.risks || []).join("，") || "暂无"}</p>
      <p>建议动作：${(item.suggested_actions || []).join("；")}</p>
      <small>毛利：${item.gross_margin ?? "-"}｜活动毛利：${item.activity_margin ?? "-"}｜库存：${item.stock ?? "-"}</small>
    </div>
  `).join("");

  const customerCards = data.customer_segmentation.map((item) => `
    <div class="result-card">
      <h3>${item.customer_id} - ${item.segment} ${badge(item.risk_level)}</h3>
      <p>标签：${(item.tags || []).join("，") || "暂无"}</p>
      <p>建议动作：${(item.recommended_actions || []).join("；")}</p>
    </div>
  `).join("");

  view().innerHTML = `
    <section class="page-section"><h2>商品诊断</h2><div class="result-list">${productCards}</div></section>
    <section class="page-section"><h2>客户分层</h2><div class="result-list">${customerCards}</div></section>
  `;
}

function renderTasks(data) {
  const overrides = data.task_status_overrides || {};
  const rows = data.rpa_tasks.map((task) => {
    const override = overrides[task.task_id] || {};
    const approvalStatus = override.approval_status || task.approval_status || "pending";
    return `
      <div class="task-row">
        <div>
          <strong>${task.task_id}</strong>
          <p>${task.ai_suggestion}</p>
        </div>
        <span>${task.task_type}</span>
        ${badge(task.risk_level)}
        ${statusBadge(approvalStatus)}
        <small>自动执行：${task.auto_execution_allowed}</small>
      </div>
    `;
  }).join("");

  view().innerHTML = `<section class="page-section"><h2>任务草案</h2><div class="task-table">${rows}</div></section>`;
}

function renderApprovals(data) {
  const overrides = data.task_status_overrides || {};
  const tasks = (data.approval_required_tasks || data.rpa_tasks).filter((task) => task.requires_approval !== false);
  const cards = tasks.map((task) => {
    const override = overrides[task.task_id] || {};
    const approvalStatus = override.approval_status || task.approval_status || "pending";
    return `
      <div class="result-card">
        <h3>${task.task_id} ${badge(task.risk_level)}</h3>
        <p>${task.ai_suggestion || task.task_type}</p>
        <p>审批状态：${approvalStatus}｜自动执行：${task.auto_execution_allowed}</p>
        <div class="task-actions">
          <button onclick="approveTask('${task.task_id}')">确认</button>
          <button class="secondary" onclick="rejectTask('${task.task_id}')">拒绝</button>
        </div>
      </div>
    `;
  }).join("");

  view().innerHTML = `<section class="page-section"><h2>待人工确认</h2><div class="result-list">${cards}</div></section>`;
}

async function renderReports() {
  if (state.apiMode && !state.reportText) {
    try {
      const response = await fetch("/api/reports/demo");
      state.reportText = await response.text();
    } catch (error) {
      state.reportText = "API 报告读取失败，当前展示本地报告占位。";
    }
  }
  view().innerHTML = `
    <section class="page-section">
      <h2>报告输出</h2>
      <div class="report-preview"><pre>${state.reportText || "运行 API 后可查看 Markdown 报告。当前可导出商品诊断、客户分层、售后归因和任务草案。"}</pre></div>
    </section>
  `;
}

function renderKnowledge(data) {
  const items = Object.entries(data.rag_context || {}).map(([key, values]) => {
    const first = values && values[0] ? values[0] : {};
    return `
      <div class="result-card">
        <h3>${key}</h3>
        <p>${first.snippet || "已召回相关知识片段"}</p>
        <small>来源：${first.source || "knowledge_base"}</small>
      </div>
    `;
  }).join("");
  view().innerHTML = `<section class="page-section"><h2>RAG 依据</h2><div class="result-list">${items}</div></section>`;
}

async function updateTask(taskId, action) {
  if (!state.apiMode) {
    alert("当前为本地样例模式。启动 FastAPI 后可记录确认 / 拒绝状态。");
    return;
  }
  const response = await fetch(`/api/approvals/${taskId}/${action}`, { method: "POST" });
  if (!response.ok) {
    alert("任务状态更新失败");
    return;
  }
  await refreshAndRender();
}

async function validateImportAndRender() {
  await refreshImportStatus(false);
  await renderRoute();
}

async function importMockAndRender() {
  await refreshImportStatus(true);
  await renderRoute();
}

async function refreshAndRender() {
  await refreshWorkflow();
  await renderRoute();
}

window.approveTask = (taskId) => updateTask(taskId, "approve");
window.rejectTask = (taskId) => updateTask(taskId, "reject");
window.refreshAndRender = refreshAndRender;
window.validateImportAndRender = validateImportAndRender;
window.importMockAndRender = importMockAndRender;

document.getElementById("refreshBtn").addEventListener("click", refreshAndRender);
window.addEventListener("hashchange", renderRoute);

refreshAndRender();
