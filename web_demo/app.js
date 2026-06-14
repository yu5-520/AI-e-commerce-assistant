const mockState = {
  erpLoaded: false,
  diagnosisReady: false,
  taskReady: false,
};

const erpSummary = {
  products: 3,
  orders: 4,
  inventory: 3,
  refunds: 2,
  highlights: [
    "P001 遮阳伞：库存 200，活动价 19.9，适合检查活动毛利。",
    "P003 护腰坐垫：敏感类目且存在退款，需要进入合规和售后归因。",
    "订单数据覆盖自然搜索、活动、付费推广等来源。",
  ],
};

const crmSummary = {
  customers: 4,
  tags: 6,
  interactions: 4,
  highlights: [
    "C001：高价值客户，具备复购潜力。",
    "C003：沉睡客户，建议低频召回，不宜频繁打扰。",
    "C004：售后敏感客户，优先售后归因，不直接营销触达。",
  ],
};

const diagnosis = [
  {
    title: "P001 遮阳伞",
    level: "medium",
    summary: "库存偏高且活动价接近保本线，建议生成 SKU 价格建议表，并在活动报名之前人工确认。",
    evidence: "RAG 召回：活动价需要结合成本、物流、退款损耗判断，不建议低于保本线参与活动。",
  },
  {
    title: "P003 护腰坐垫",
    level: "high",
    summary: "敏感类目 + 退款反馈，建议优先做售后归因和合规检查，暂不建议自动生成强营销话术。",
    evidence: "RAG 召回：健康、功效、售后敏感场景需要避免功效承诺和诱导好评。",
  },
  {
    title: "C004 售后敏感客户",
    level: "high",
    summary: "退款次数和负面互动较高，建议生成售后归因表和客服 SOP 草案，不自动触达客户。",
    evidence: "CRM 分层：售后敏感 + 流失风险；Human-in-the-loop 必须开启。",
  },
];

const tasks = [
  {
    id: "TASK_PRODUCT_DAILY_001",
    type: "daily_report",
    level: "low",
    approval: "pending",
    action: "生成商品经营日报和下一轮复盘摘要。",
  },
  {
    id: "TASK_SKU_PRICE_001",
    type: "sku_price_table",
    level: "medium",
    approval: "pending",
    action: "生成 SKU 价格建议表，标记保本线、活动价风险和人工确认项。",
  },
  {
    id: "TASK_CRM_AFTER_SALES_004",
    type: "after_sales_analysis",
    level: "high",
    approval: "pending",
    action: "生成售后归因表，不自动营销触达。",
  },
];

function setStatus(id, text, tone = "") {
  const node = document.getElementById(id);
  node.textContent = text;
  node.className = tone;
}

function badge(level) {
  const label = level === "high" ? "高风险" : level === "medium" ? "中风险" : "低风险";
  return `<span class="badge ${level}">${label}</span>`;
}

function renderList(items) {
  return `<ul class="metric-list">${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

function markStep(stepIndex) {
  document.querySelectorAll(".flow-step").forEach((node, index) => {
    node.classList.toggle("active", index === stepIndex);
  });
}

function loadData() {
  mockState.erpLoaded = true;
  markStep(0);
  setStatus("erpStatus", "已导入");
  setStatus("crmStatus", "已导入");

  document.getElementById("erpSummary").innerHTML = `
    <ul class="metric-list">
      <li>商品表：${erpSummary.products} 条</li>
      <li>订单表：${erpSummary.orders} 条</li>
      <li>库存表：${erpSummary.inventory} 条</li>
      <li>退款表：${erpSummary.refunds} 条</li>
    </ul>
    <p>${erpSummary.highlights.join("<br>")}</p>
  `;

  document.getElementById("crmSummary").innerHTML = `
    <ul class="metric-list">
      <li>客户表：${crmSummary.customers} 条</li>
      <li>客户标签：${crmSummary.tags} 条</li>
      <li>互动记录：${crmSummary.interactions} 条</li>
    </ul>
    <p>${crmSummary.highlights.join("<br>")}</p>
  `;
}

function runDiagnosis() {
  if (!mockState.erpLoaded) loadData();
  mockState.diagnosisReady = true;
  markStep(1);
  setStatus("diagnosisStatus", "已生成");

  document.getElementById("diagnosisResult").innerHTML = `
    <div class="result-list">
      ${diagnosis
        .map(
          (item) => `
          <div class="result-item">
            <h3>${item.title} ${badge(item.level)}</h3>
            <p>${item.summary}</p>
            <small>${item.evidence}</small>
          </div>
        `
        )
        .join("")}
    </div>
  `;
}

function generateTasks() {
  if (!mockState.diagnosisReady) runDiagnosis();
  mockState.taskReady = true;
  markStep(2);
  setStatus("taskStatus", "待人工确认");

  document.getElementById("taskResult").innerHTML = `
    <div class="result-list">
      ${tasks
        .map(
          (task) => `
          <div class="result-item">
            <h3>${task.id} ${badge(task.level)}</h3>
            <p>类型：${task.type}</p>
            <p>动作：${task.action}</p>
            <small>审批状态：${task.approval}；自动执行：false</small>
          </div>
        `
        )
        .join("")}
    </div>
  `;
}

function showApproval() {
  if (!mockState.taskReady) generateTasks();
  const approvalItems = tasks
    .filter((task) => task.level !== "low")
    .map((task) => `${task.id}：${task.action}`);

  document.getElementById("taskResult").innerHTML += `
    <div class="result-item">
      <h3>必须人工确认的任务</h3>
      ${renderList(approvalItems)}
      <p>当前 Demo 不会自动执行改价、活动报名、客户触达、退款处理等高风险动作。</p>
    </div>
  `;
}

document.getElementById("loadDataBtn").addEventListener("click", loadData);
document.getElementById("diagnosisBtn").addEventListener("click", runDiagnosis);
document.getElementById("taskBtn").addEventListener("click", generateTasks);
document.getElementById("approvalBtn").addEventListener("click", showApproval);
