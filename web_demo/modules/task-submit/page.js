(function () {
  const s = (value) => AppShell.escape(value ?? "");
  let taskId = "";
  let report = null;
  let evidence = null;
  let notice = "";

  function arr(value) { return Array.isArray(value) ? value.filter(Boolean) : []; }
  function task() { return report?.relatedTask || {}; }
  function steps() { return arr(report?.operatorSopSteps || report?.sopSteps || report?.suggestedActions || report?.operationChecklist || task().sopSteps); }
  function neededFields() {
    const templateFields = arr(evidence?.template?.fields);
    const gateFields = arr((task().actionAuthorization || task().v1282ActionGate || {}).operatorFactFields);
    const dataNeeded = arr(report?.dataNeeded).map((item) => item.title || item.summary || item).filter(Boolean);
    const base = [...templateFields, ...gateFields, ...dataNeeded];
    const fallback = ["处理动作", "处理说明", "影响范围", "执行时间"];
    return Array.from(new Set((base.length ? base : fallback).map((item) => String(item || "").trim()).filter(Boolean))).slice(0, 8);
  }
  function uploadFields() {
    const text = [report?.title, report?.warningSummary, task().riskDomain, task().actionType, task().taskType, ...(task().judgmentTags || [])].join(" ");
    if (/主图|标题|点击|素材|创意|转化/.test(text)) return ["上传修改前截图", "上传修改后截图", "上传测试范围截图"];
    if (/库存|补货|可售/.test(text)) return ["上传库存截图", "上传补货或仓库确认截图"];
    if (/售后|退款|客服|差评/.test(text)) return ["上传退款原因截图", "上传客服核实截图"];
    return ["上传处理截图", "上传数据凭证"];
  }
  function fieldName(label, index) { return `field_${index}_${String(label).replace(/[^\w\u4e00-\u9fa5]/g, "_")}`; }
  function renderUpload(label, index) {
    return `<label class="submit-upload-card"><span>${s(label)}</span><input type="file" data-upload-field="${s(label)}" data-upload-index="${index}" accept="image/*,.pdf,.xlsx,.xls,.csv" /><em data-upload-name="${index}">未选择文件</em></label>`;
  }
  function renderField(label, index) {
    return `<label class="submit-field"><span>${s(label)}</span><textarea rows="2" name="${s(fieldName(label, index))}" data-field-label="${s(label)}" placeholder="填写${s(label)}"></textarea></label>`;
  }
  function renderSteps() {
    const list = steps();
    if (!list.length) return "";
    return `<section class="page-section"><div class="section-header"><h3>Agent SOP确认</h3><span class="status-badge">运营只执行</span></div><ol class="action-step-list">${list.map((item) => `<li>${s(item.title || item.action || item.summary || item)}</li>`).join("")}</ol></section>`;
  }
  function renderForm() {
    const uploads = uploadFields();
    const fields = neededFields();
    return `<section class="page-section task-submit-section"><div class="section-header"><h3>提交处理材料</h3><span class="status-badge">提交后系统复盘</span></div><form id="taskSubmitForm" class="task-submit-form">
      <div class="submit-upload-grid">${uploads.map(renderUpload).join("")}</div>
      <div class="submit-field-grid">${fields.map(renderField).join("")}</div>
      <label class="submit-field full"><span>处理总结</span><textarea rows="4" name="summary" placeholder="说明已执行的Agent SOP动作、影响范围、已上传的截图或数据凭证"></textarea></label>
      <label class="submit-field full"><span>处理结果</span><textarea rows="3" name="result" placeholder="例如：已更换标题A并保留原标题B对照；提交后由系统等待下一次报表更新自动复盘"></textarea></label>
      <div class="report-actions"><button type="submit">确认提交材料</button><button type="button" class="secondary" data-back-task>返回任务列表</button><button type="button" class="secondary" data-open-detail="${s(taskId)}">查看SOP详情</button></div>
    </form></section>`;
  }
  function renderPage() {
    if (!taskId) return `<section class="page-section"><h3>缺少任务ID</h3><p>请从任务列表重新进入提交页。</p><button data-back-task>返回任务列表</button></section>`;
    const t = task();
    const title = report?.title || t.title || t.productTitle || "任务提交";
    const status = report?.taskStatus || t.status || "处理中";
    return `<section class="report-hero"><div><p class="eyebrow">TASK SUBMIT · V12.11</p><h2>${s(title)}</h2><p>${s(report?.warningSummary || t.reason || "按Agent SOP提交处理材料，后续报表更新后由系统自动复盘。")}</p></div><div class="report-hero-side"><span>当前状态</span><strong>${s(status)}</strong><small>${s(t.store || t.storeName || "任务池")}</small></div></section>${notice ? AppShell.notice("提交结果", notice) : ""}${renderSteps()}${renderForm()}`;
  }
  function collectPayload(form) {
    const fields = {};
    form.querySelectorAll("[data-field-label]").forEach((node) => {
      const label = node.dataset.fieldLabel;
      const value = node.value.trim();
      if (label && value) fields[label] = value;
    });
    const attachments = Array.from(form.querySelectorAll("[data-upload-field]")).map((input) => ({
      field: input.dataset.uploadField,
      filename: input.files?.[0]?.name || "",
      size: input.files?.[0]?.size || 0,
      type: input.files?.[0]?.type || "",
    })).filter((item) => item.filename);
    const summary = form.summary?.value?.trim() || "运营已提交Agent SOP执行材料，等待系统自动复盘。";
    const result = form.result?.value?.trim() || "处理材料已提交，后续报表更新后系统自动计算复盘结果。";
    return { summary, note: summary, result, fields, formFields: fields, attachments, evidenceLinks: attachments, action: task().actionType || task().taskType || "运营处理", enterRecap: true, operatorManualRecapRequired: false };
  }

  window.TaskSubmitPage = {
    route: "task-submit",
    title: "提交材料",
    async render(ctx) {
      taskId = ctx?.state?.taskId || taskId || "";
      notice = "";
      report = taskId ? await AppApi.taskReport(taskId).catch(() => null) : null;
      evidence = taskId ? await AppApi.taskEvidence(taskId).catch(() => null) : null;
      return renderPage();
    },
    mount(ctx) {
      ctx.delegate("[data-back-task]", "click", () => AppRouter.navigate("business-actions", taskId ? { focusTaskId: taskId } : null));
      ctx.delegate("[data-open-detail]", "click", (_, node) => AppRouter.navigate("task-report", { taskId: node.dataset.openDetail }));
      ctx.delegate("[data-upload-field]", "change", (_, node) => {
        const label = document.querySelector(`[data-upload-name="${CSS.escape(node.dataset.uploadIndex || "")}"]`);
        if (label) label.textContent = node.files?.[0]?.name || "未选择文件";
      });
      ctx.delegate("#taskSubmitForm", "submit", async (event, form) => {
        event.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        const original = button.textContent;
        button.disabled = true;
        button.textContent = "提交中";
        try {
          const result = await AppApi.submitEvidenceTodo(taskId, collectPayload(form));
          if (result?.task?.id) window.AppTaskStore?.upsert?.(result.task);
          await AppApi.refreshTaskState().catch(() => null);
          notice = "处理材料已提交，任务进入等待系统自动复盘链路。";
          AppRouter.navigate("business-report");
        } catch (error) {
          notice = error?.message || "提交失败，请补充材料后重试。";
          button.disabled = false;
          button.textContent = original;
          AppShell.setView(renderPage());
          window.TaskSubmitPage.mount(ctx);
        }
      });
    },
  };
})();
