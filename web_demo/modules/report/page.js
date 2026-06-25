(function () {
  const s = (value) => AppShell.escape(value ?? "");
  let lastImportSync = null;
  let sourceMessage = "主链路优先：接口同步负责日常更新，手动上传只用于补数。";

  const FALLBACK_SOURCES = [
    { sourceId: "erp", label: "ERP 接口", priority: "primary", displayStatus: "待配置", cadence: "15分钟 / 1小时", dataScope: ["商品", "订单", "库存", "成本"], targetModules: ["总览", "经营", "任务", "数据", "日志"], actionLabel: "同步 ERP" },
    { sourceId: "crm", label: "CRM 接口", priority: "primary", displayStatus: "待配置", cadence: "1小时 / 每日", dataScope: ["客户", "售后", "退款", "标签"], targetModules: ["总览", "经营", "任务", "数据", "日志"], actionLabel: "同步 CRM" },
    { sourceId: "platform", label: "平台后台 API", priority: "primary", displayStatus: "待配置", cadence: "15分钟 / 1小时", dataScope: ["商品", "订单", "评价", "售后"], targetModules: ["总览", "经营", "任务", "数据", "日志"], actionLabel: "同步平台" },
    { sourceId: "ads", label: "广告后台 API", priority: "primary", displayStatus: "待配置", cadence: "15分钟 / 每日", dataScope: ["投放", "ROI", "点击", "转化"], targetModules: ["总览", "经营", "任务", "数据", "日志"], actionLabel: "同步广告" },
    { sourceId: "manual_upload", label: "手动上传", priority: "backup", displayStatus: "备用入口", cadence: "临时补录", dataScope: ["Excel", "CSV", "JSON"], targetModules: ["总览", "经营", "任务", "数据", "日志"], actionLabel: "上传文件" },
  ];

  function realRecords(payload) {
    if (Array.isArray(payload?.syncRecords)) return payload.syncRecords;
    const groups = Array.isArray(payload?.reportGroups) ? payload.reportGroups : [];
    return groups.flatMap((group) => (group.reports || []).filter((item) => item.latestDataVersion || item.status === "已导入"));
  }

  function latestReport(payload) {
    const records = realRecords(payload);
    const first = records[0] || {};
    const sync = lastImportSync || payload?.v104ImportTaskSync || window.AppApi?.status?.lastImportSync;
    if (!payload?.hasData && !sync && !records.length) {
      return { label: "等待同步", status: "待同步", taskCount: 0, rows: 0, message: "暂无同步数据", modules: [] };
    }
    return {
      label: sync?.datasetNames?.join(" / ") || first.name || first.label || payload?.v3?.latestDataVersion || "等待同步",
      status: sync?.status === "completed" ? "已更新" : first.status || (payload?.v3?.latestDataVersion ? "已更新" : "待同步"),
      taskCount: sync?.createdTaskCount ?? first.createdTaskCount ?? first.taskCount ?? payload?.recentAlerts?.length ?? 0,
      rows: sync?.rowCount ?? first.rows ?? first.totalRows ?? 0,
      message: sync?.userMessage || sync?.summary,
      modules: sync?.updatedModuleLabels || [],
    };
  }

  function syncStrip(latest) {
    const modules = latest.modules.length ? latest.modules.join(" / ") : "总览 / 经营 / 任务 / 数据 / 日志";
    return `<section class="v102-status-strip v104-import-sync-strip"><strong>${s(latest.status)}</strong><span>${s(latest.message || `已更新，生成 ${latest.taskCount} 个任务`)}</span><span>同步：${s(modules)}</span><button type="button" class="secondary" data-open-tasks>查看任务</button></section>`;
  }

  function recordRow(item) {
    return `<article class="report-record-row"><strong>${s(item.name || item.label || "同步记录")}</strong><span>${s(item.status || "已处理")}</span><span>生成 ${s(item.createdTaskCount ?? item.taskCount ?? 0)} 个任务</span><button type="button" data-report-task="${s(item.id || item.name || "report")}">查看任务</button></article>`;
  }

  function emptyRecordRow() {
    return `<article class="report-record-row"><strong>暂无同步记录</strong><span>等待接口同步</span><span>清空后不保留占位记录</span><button type="button" data-source-sync="erp">同步 ERP</button></article>`;
  }

  function sourceCard(item) {
    const isBackup = item.priority === "backup";
    const scope = (item.dataScope || []).join(" / ") || "经营数据";
    const modules = (item.targetModules || []).join(" / ") || "总览 / 经营 / 任务 / 数据 / 日志";
    const statusClass = isBackup ? "warning" : "good";
    const action = isBackup
      ? `<button type="button" class="secondary" data-open-upload>选择文件</button>`
      : `<button type="button" data-source-sync="${s(item.sourceId)}">${s(item.actionLabel || "同步数据")}</button><button type="button" class="secondary" data-open-source-config="${s(item.sourceId)}">接口配置</button>`;
    return `<article class="platform-card data-source-card">
      <div class="platform-head"><div><span class="status-dot ${statusClass}"></span><strong>${s(item.label)}</strong></div><span>${s(isBackup ? "备用" : "主链路")}</span></div>
      <div class="platform-numbers"><div><small>状态</small><b>${s(item.displayStatus || "待配置")}</b></div><div><small>频率</small><b>${s(item.cadence || "按需")}</b></div></div>
      <footer>${s(scope)} → ${s(modules)}</footer>
      <div class="task-actions">${action}</div>
    </article>`;
  }

  function uploadSection() {
    return `<section class="page-section v102-main-section"><div class="section-header"><h3>备用上传</h3><span class="status-badge">兜底入口</span></div>
      <input type="file" data-manual-file-input accept=".xlsx,.xlsm,.xls,.csv,.json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv,application/json" style="display:none" />
      <div class="report-record-list">
        <article class="report-record-row"><strong>手动上传 Excel / CSV / JSON</strong><span>备用补数</span><span>接口未开通或异常时使用</span><button type="button" class="secondary" data-open-upload>选择文件</button></article>
        <article class="report-record-row"><strong>演示数据同步</strong><span>Demo</span><span>生成测试任务和记录</span><button type="button" class="secondary" data-import-demo>运行演示</button></article>
        <article class="report-record-row"><strong>清空测试数据</strong><span>Demo</span><span>重置总览、经营、任务、数据和日志</span><button type="button" class="secondary" data-reset-demo>清空数据</button></article>
      </div>
    </section>`;
  }

  function parseCsv(text) {
    const rows = [];
    let row = [];
    let field = "";
    let inQuotes = false;
    for (let index = 0; index < text.length; index += 1) {
      const char = text[index];
      const next = text[index + 1];
      if (char === '"') {
        if (inQuotes && next === '"') { field += '"'; index += 1; }
        else inQuotes = !inQuotes;
      } else if (char === "," && !inQuotes) {
        row.push(field);
        field = "";
      } else if ((char === "\n" || char === "\r") && !inQuotes) {
        if (char === "\r" && next === "\n") index += 1;
        row.push(field);
        if (row.some((cell) => String(cell).trim() !== "")) rows.push(row);
        row = [];
        field = "";
      } else {
        field += char;
      }
    }
    row.push(field);
    if (row.some((cell) => String(cell).trim() !== "")) rows.push(row);
    const headers = (rows.shift() || []).map((header) => String(header || "").trim());
    if (!headers.length) return [];
    return rows.map((values) => {
      const item = {};
      headers.forEach((header, index) => { if (header) item[header] = values[index] ?? ""; });
      return item;
    }).filter((item) => Object.values(item).some((value) => String(value).trim() !== ""));
  }

  async function parseUploadFile(file) {
    const text = await file.text();
    if (/\.json$/i.test(file.name || "")) {
      const payload = JSON.parse(text);
      const rows = Array.isArray(payload) ? payload : payload.rows || payload.data || [];
      if (!Array.isArray(rows)) throw new Error("JSON 需要是数组，或包含 rows/data 数组。");
      return rows.filter((item) => item && typeof item === "object");
    }
    return parseCsv(text);
  }

  function uploadSummary(result, file) {
    const meta = result?.uploadMeta || {};
    const rows = meta.totalRows ?? result?.rowCount ?? result?.v104ImportTaskSync?.rowCount ?? 0;
    const sheetText = meta.sheetCount ? `，识别 ${meta.sheetCount} 个 Sheet` : "";
    return `备用上传完成：${file.name}，读取 ${rows} 行${sheetText}。`;
  }

  function setSourceMessage(text) {
    sourceMessage = text;
    const node = AppShell.view()?.querySelector("[data-source-message]");
    if (node) node.textContent = text;
  }

  window.ReportPage = {
    route: "data-check",
    title: "数据",
    async render() {
      const [payload, connectionPayload] = await Promise.all([AppApi.report(), AppApi.dataSourceConnections?.()]);
      const latest = latestReport(payload || {});
      const records = realRecords(payload || {});
      const sources = connectionPayload?.sources?.length ? connectionPayload.sources : FALLBACK_SOURCES;
      const primarySources = sources.filter((item) => item.priority !== "backup");
      return `<section class="v102-hero report-workbench"><div><h2>经营数据接入</h2><strong>ERP、CRM、平台后台和广告后台是主链路；手动上传用于补数。</strong></div></section>
        ${syncStrip(latest)}
        <section class="page-section v102-main-section"><div class="section-header"><h3>已接入数据源</h3><span class="status-badge">接口主链路</span></div><div class="platform-grid">${primarySources.map(sourceCard).join("")}</div></section>
        ${uploadSection()}
        <section class="page-section v102-main-section"><div class="section-header"><h3>同步记录</h3><button type="button" class="secondary" data-reset-demo>清空测试数据</button></div><div class="report-record-list">${records.length ? records.map(recordRow).join("") : emptyRecordRow()}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-source-sync]", "click", async (event, target) => {
        const sourceId = target.getAttribute("data-source-sync") || "erp";
        const oldText = target.textContent;
        target.disabled = true;
        target.textContent = "同步中";
        setSourceMessage(`正在同步 ${sourceId.toUpperCase()} 数据源。`);
        const result = await AppApi.syncDataSource(sourceId);
        if (!result) {
          target.disabled = false;
          target.textContent = oldText;
          setSourceMessage("接口同步失败：请确认后端服务已更新。");
          return;
        }
        await AppApi.refreshAfterDataImport(result);
        lastImportSync = result?.v104ImportTaskSync || window.AppApi?.status?.lastImportSync || null;
        AppRouter.schedule("v1012-source-sync");
      });
      ctx.delegate("[data-open-source-config]", "click", (event, target) => {
        const sourceId = target.getAttribute("data-open-source-config") || "数据源";
        setSourceMessage(`${sourceId.toUpperCase()} 接口配置入口已预留。`);
      });
      ctx.delegate("[data-open-upload]", "click", () => AppShell.view()?.querySelector("[data-manual-file-input]")?.click());
      ctx.delegate("[data-import-demo]", "click", async (event, target) => {
        const oldText = target.textContent;
        target.disabled = true;
        target.textContent = "运行中";
        const result = await AppApi.importMockAlerts();
        await AppApi.refreshAfterDataImport(result);
        lastImportSync = result?.v104ImportTaskSync || window.AppApi?.status?.lastImportSync || null;
        AppRouter.schedule("v1012-demo-sync");
      });
      ctx.delegate("[data-reset-demo]", "click", async (event, target) => {
        if (!window.confirm("清空演示测试数据？这会重置总览、经营、任务、数据和日志。")) return;
        const oldText = target.textContent;
        target.disabled = true;
        target.textContent = "清空中";
        await AppApi.resetRuntimeData(true);
        lastImportSync = null;
        setSourceMessage("测试数据已清空。");
        await AppApi.refreshAfterDataImport({ v104ImportTaskSync: null });
        target.disabled = false;
        target.textContent = oldText;
        AppRouter.schedule("v1012-reset-demo");
      });
      ctx.on("[data-manual-file-input]", "change", async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;
        setSourceMessage(`正在上传并解析备用文件：${file.name}`);
        try {
          let result = await AppApi.uploadReportFile?.(file, "auto", "manual_upload");
          if (!result && /\.(csv|json)$/i.test(file.name || "")) {
            const rows = await parseUploadFile(file);
            if (!rows.length) throw new Error("没有读取到有效数据行。");
            result = await AppApi.confirmReportImport("auto", rows, {}, "manual_upload");
          }
          if (!result) throw new Error("后端导入接口不可用，或文件格式暂未被当前服务支持。");
          await AppApi.refreshAfterDataImport(result);
          lastImportSync = result?.v104ImportTaskSync || window.AppApi?.status?.lastImportSync || null;
          setSourceMessage(uploadSummary(result, file));
          AppRouter.schedule("v1012-manual-upload");
        } catch (error) {
          setSourceMessage(`备用上传失败：${error.message || error}`);
        } finally {
          event.target.value = "";
        }
      });
      ctx.delegate("[data-open-tasks]", "click", () => AppRouter.navigate("business-actions"));
      ctx.delegate("[data-report-task]", "click", () => AppRouter.navigate("business-actions"));
      const onSync = (event) => { lastImportSync = event.detail?.sync || lastImportSync; };
      window.addEventListener("v104-import-sync", onSync);
      ctx.addCleanup(() => window.removeEventListener("v104-import-sync", onSync));
    },
  };
})();
