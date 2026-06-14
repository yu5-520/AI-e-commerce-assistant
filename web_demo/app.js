const state = {
  apiData: null,
  apiMode: false,
  erpLoaded: false,
  diagnosisReady: false,
  taskReady: false,
};

const fallbackData = {
  summary: {
    product_count: 3,
    customer_count: 4,
    rpa_task_count: 7,
    approval_required_count: 7,
  },
  product_diagnosis: [
    {
      product_id: "P001",
      product_name: "遮阳伞",
      risk_level: "medium",
      risks: ["high_inventory_low_order_risk", "activity_price_margin_risk"],
      suggested_actions: ["生成 SKU 价格建议表", "活动报名前人工确认"],
    },
    {
      product_id: "P003",
      product_name: "护腰坐垫",
      risk_level: "high",
      risks: ["sensitive_category_compliance_risk", "refund_abnormal_risk"],
      suggested_actions: ["进入售后归因工作流", "先做合规检查"],
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

fallbackData.approval_required_tasks = fallbackData.rpa_tasks.filter((task) => task.requires_approval !== false);

function setStatus(id, text) {
  document.getElementById(id).textContent = text;
}

function badge(level) {
  const label = level === "high" ? "高风险" : level === "medium" ? "中风险" : "低风险";
  return `<span class="badge ${level}">${label}</span>`;
}

function renderList(items) {
  if (!items.length) return "<p>暂无。</p>";
  return `<ul class="metric-list">${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

function markStep(stepIndex) {
  document.querySelectorAll(".flow-step").forEach((node, index) => {
    node.classList.toggle("active", index === stepIndex);
  });
}

function getData() {
  return state.apiData || fallbackData;
}

async function fetchApiData() {
  try {
    const response = await fetch("/api/demo/run");
    if (!response.ok) throw new Error(`API ${response.status}`);
    state.apiData = await response.json();
    state.apiMode = true;
    return state.apiData;
  } catch (error) {
    state.apiData = fallbackData;
    state.apiMode = false;
    return fallbackData;
  }
}

function renderDataSummary(data) {
  const summary = data.summary || {};
  setStatus("erpStatus", state.apiMode ? "API 已导入" : "本地样例");
  setStatus("crmStatus", state.apiMode ? "API 已导入" : "本地样例");

  document.getElementById("erpSummary").innerHTML = `
    <ul class="metric-list">
      <li>商品诊断对象：${summary.product_count || data.product_diagnosis.length} 个</li>
      <li>RPA 任务草案：${summary.rpa_task_count || data.rpa_tasks.length} 个</li>
      <li>需人工确认任务：${summary.approval_required_count || data.approval_required_tasks.length} 个</li>
    </ul>
    <p>${state.apiMode ? "已连接 FastAPI，当前展示真实 Python Mock Workflow 输出。" : "当前使用前端内置样例数据；启动 FastAPI 后会自动切换到 API 输出。"}</p>
  `;

  document.getElementById("crmSummary").innerHTML = `
    <ul class="metric-list">
      <li>客户分层对象：${summary.customer_count || data.customer_segmentation.length} 个</li>
      <li>高风险客户：${data.customer_segmentation.filter((item) => item.risk_level === "high").length} 个</li>
      <li>禁止自动触达：true</li>
    </ul>
    <p>CRM 数据使用脱敏 Mock 数据，不保存真实姓名、手机号、微信号或地址。</p>
  `;
}

async function loadData() {
  setStatus("erpStatus", "导入中...");
  setStatus("crmStatus", "导入中...");
  const data = await fetchApiData();
  state.erpLoaded = true;
  markStep(0);
  renderDataSummary(data);
}

function renderDiagnosis(data) {
  const productItems = data.product_diagnosis.map((item) => `
    <div class="result-item">
      <h3>${item.product_id} - ${item.product_name} ${badge(item.risk_level)}</h3>
      <p>风险标签：${(item.risks || []).join("，") || "暂无"}</p>
      <p>建议动作：${(item.suggested_actions || []).join("；")}</p>
    </div>
  `);

  const customerItems = data.customer_segmentation.map((item) => `
    <div class="result-item">
      <h3>${item.customer_id} - ${item.segment} ${badge(item.risk_level)}</h3>
      <p>标签：${(item.tags || []).join("，") || "暂无"}</p>
      <p>建议动作：${(item.recommended_actions || []).join("；")}</p>
    </div>
  `);

  const ragItems = Object.entries(data.rag_context || {}).map(([key, values]) => {
    const first = values && values[0] ? values[0] : {};
    return `<li>${key}：${first.source || "knowledge_base"}｜${first.snippet || "已召回相关依据"}</li>`;
  });

  document.getElementById("diagnosisResult").innerHTML = `
    <div class="result-list">
      ${productItems.join("")}
      ${customerItems.join("")}
      <div class="result-item">
        <h3>RAG 召回依据</h3>
        ${renderList(ragItems)}
      </div>
    </div>
  `;
}

async function runDiagnosis() {
  if (!state.erpLoaded) await loadData();
  state.diagnosisReady = true;
  markStep(1);
  setStatus("diagnosisStatus", state.apiMode ? "API 已生成" : "本地样例");
  renderDiagnosis(getData());
}

function renderTasks(data) {
  const overrides = data.task_status_overrides || {};
  const taskCards = data.rpa_tasks.map((task) => {
    const override = overrides[task.task_id] || {};
    const approvalStatus = override.approval_status || task.approval_status || "pending";
    return `
      <div class="result-item">
        <h3>${task.task_id} ${badge(task.risk_level)}</h3>
        <p>类型：${task.task_type}</p>
        <p>动作：${task.ai_suggestion}</p>
        <small>审批状态：${approvalStatus}；自动执行：${task.auto_execution_allowed}</small>
        <div class="task-actions">
          <button onclick="approveTask('${task.task_id}')">确认</button>
          <button onclick="rejectTask('${task.task_id}')">拒绝</button>
        </div>
      </div>
    `;
  });

  document.getElementById("taskResult").innerHTML = `<div class="result-list">${taskCards.join("")}</div>`;
}

async function generateTasks() {
  if (!state.diagnosisReady) await runDiagnosis();
  state.taskReady = true;
  markStep(2);
  setStatus("taskStatus", state.apiMode ? "API 待人工确认" : "本地样例");
  renderTasks(getData());
}

function showApproval() {
  if (!state.taskReady) return generateTasks().then(showApproval);
  const data = getData();
  const approvalItems = (data.approval_required_tasks || data.rpa_tasks)
    .filter((task) => task.risk_level !== "low" || task.requires_approval !== false)
    .map((task) => `${task.task_id}：${task.ai_suggestion || task.task_type}`);

  document.getElementById("taskResult").innerHTML += `
    <div class="result-item">
      <h3>必须人工确认的任务</h3>
      ${renderList(approvalItems)}
      <p>当前 Demo 不会自动执行改价、活动报名、客户触达、退款处理等高风险动作。</p>
    </div>
  `;
}

async function updateTask(taskId, action) {
  if (!state.apiMode) {
    alert("当前为本地样例模式。启动 FastAPI 后可记录确认 / 拒绝状态。");
    return;
  }
  const response = await fetch(`/api/tasks/${taskId}/${action}`, { method: "POST" });
  if (!response.ok) {
    alert("任务状态更新失败");
    return;
  }
  await loadData();
  await runDiagnosis();
  await generateTasks();
}

window.approveTask = (taskId) => updateTask(taskId, "approve");
window.rejectTask = (taskId) => updateTask(taskId, "reject");

document.getElementById("loadDataBtn").addEventListener("click", loadData);
document.getElementById("diagnosisBtn").addEventListener("click", runDiagnosis);
document.getElementById("taskBtn").addEventListener("click", generateTasks);
document.getElementById("approvalBtn").addEventListener("click", showApproval);
