(function () {
  const s = (value) => AppShell.escape(value ?? "-");

  async function loadJson(path, fallback = null) {
    try {
      const response = await fetch(path, { method: "GET", headers: { Accept: "application/json", "X-Mock-User-Id": window.AppApi?.getCurrentUserId?.() || "U001" } });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.warn(`[system-status] fallback for ${path}`, error);
      return fallback;
    }
  }

  async function postJson(path) {
    const response = await fetch(path, { method: "POST", headers: { Accept: "application/json", "X-Mock-User-Id": window.AppApi?.getCurrentUserId?.() || "U001" } });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  function pill(text, tone = "neutral") { return `<span class="system-pill ${tone}">${s(text)}</span>`; }
  function metric(label, value, tone = "neutral") { return `<article class="system-metric"><span>${s(label)}</span><strong>${s(value)}</strong>${pill(tone === "good" ? "正常" : tone === "warn" ? "关注" : tone === "danger" ? "阻断" : "状态", tone)}</article>`; }
  function row(title, value, tone = "neutral") { return `<article class="system-layer-row"><div><strong>${s(title)}</strong><span>${s(value)}</span></div>${pill(tone, tone === "正常" || tone === "已回填" ? "good" : tone === "关注" ? "warn" : tone === "阻断" ? "danger" : "neutral")}</article>`; }

  function statusTone(status) {
    if (status === "ok") return "good";
    if (status === "object_sync_failed" || status === "dirty_runtime_residue") return "danger";
    if (status === "visible_empty") return "warn";
    return "neutral";
  }

  function statusLabel(status) {
    if (status === "object_sync_failed") return "经营对象未入库";
    if (status === "dirty_runtime_residue") return "清空不完整";
    if (status === "visible_empty") return "当前账号不可见";
    return "运行正常";
  }

  function renderTableCounts(counts = {}) {
    const entries = Object.entries(counts);
    return entries.map(([name, value]) => row(name, value, value > 0 ? "正常" : "关注")).join("") || "<p>暂无运行态表数据。</p>";
  }

  function renderBackfillResult(result) {
    if (!result) return "";
    const after = result.after || {};
    const blocked = result.status === "blocked_dirty_runtime_residue";
    return `<section class="page-section system-section"><div class="section-header"><h3>最近处理结果</h3>${pill(result.status || "completed", blocked ? "danger" : result.status === "completed" ? "good" : "warn")}</div><div class="system-layer-list">
      ${row("来源", result.source, blocked ? "阻断" : "正常")}
      ${row("处理行数", result.rowCount, result.rowCount > 0 ? "已回填" : "关注")}
      ${row("商品入库", result.operatingObjectSync?.productUpsertCount ?? 0, (result.operatingObjectSync?.productUpsertCount ?? 0) > 0 ? "已回填" : "关注")}
      ${row("店铺入库", result.operatingObjectSync?.storeUpsertCount ?? 0, (result.operatingObjectSync?.storeUpsertCount ?? 0) > 0 ? "已回填" : "关注")}
      ${row("当前可见商品", after.visibleCounts?.products ?? 0, (after.visibleCounts?.products ?? 0) > 0 ? "正常" : "关注")}
      ${row("当前可见店铺", after.visibleCounts?.stores ?? 0, (after.visibleCounts?.stores ?? 0) > 0 ? "正常" : "关注")}
      ${row("规则", result.rule || "-", blocked ? "阻断" : "正常")}
    </div></section>`;
  }

  window.SystemStatusPage = {
    route: "system-status",
    title: "系统状态",
    _backfillResult: null,
    async render() {
      const [health, diagnostics, db] = await Promise.all([
        loadJson("/api/health", {}),
        loadJson("/api/system/runtime-diagnostics", {}),
        loadJson("/api/system/db-status", {}),
      ]);
      const apiVersion = health?.version || diagnostics?.version || "11.14.0";
      const visible = diagnostics?.visibleCounts || {};
      const tableCounts = diagnostics?.tableCounts || {};
      const tone = statusTone(diagnostics?.status);
      const statusText = statusLabel(diagnostics?.status);
      const dirty = diagnostics?.dirtyRuntimeResidue;
      return `<section class="system-hero"><div><p class="eyebrow">SYSTEM STATUS · V11.14</p><h2>系统状态</h2><p>优先检查真实运行态：导入行、快照、业务信号、经营对象主档、当前账号可见商品和店铺。</p></div><div class="system-hero-side"><span>当前版本</span><strong>${s(apiVersion)}</strong><small>${s(statusText)}</small></div></section>
      <section class="system-metric-grid">
        ${metric("运行状态", statusText, tone)}
        ${metric("当前可见商品", visible.products ?? 0, dirty ? "danger" : (visible.products ?? 0) > 0 ? "good" : "warn")}
        ${metric("当前可见店铺", visible.stores ?? 0, dirty ? "danger" : (visible.stores ?? 0) > 0 ? "good" : "warn")}
        ${metric("导入行", tableCounts.imported_report_rows ?? 0, (tableCounts.imported_report_rows ?? 0) > 0 ? "good" : "warn")}
      </section>
      <section class="page-section system-section"><div class="section-header"><h3>经营对象运行诊断</h3>${pill(statusText, tone)}</div><div class="system-layer-list">
        ${row("当前账号", `${diagnostics?.currentContext?.user_id || diagnostics?.currentContext?.userId || "-"} / ${diagnostics?.currentContext?.role_id || diagnostics?.currentContext?.roleId || "-"}`, "正常")}
        ${row("business_signals_v6", tableCounts.business_signals_v6 ?? 0, (tableCounts.business_signals_v6 ?? 0) > 0 ? (dirty ? "阻断" : "正常") : "关注")}
        ${row("operating_products", tableCounts.operating_products ?? 0, (tableCounts.operating_products ?? 0) > 0 ? (dirty ? "阻断" : "正常") : "关注")}
        ${row("operating_stores", tableCounts.operating_stores ?? 0, (tableCounts.operating_stores ?? 0) > 0 ? (dirty ? "阻断" : "正常") : "关注")}
        ${row("当前账号可见商品", visible.products ?? 0, (visible.products ?? 0) > 0 && !dirty ? "正常" : "关注")}
        ${row("当前账号可见店铺", visible.stores ?? 0, (visible.stores ?? 0) > 0 && !dirty ? "正常" : "关注")}
        ${row("诊断规则", diagnostics?.rule || "经营对象主档为准", dirty || diagnostics?.objectSyncFailed ? "阻断" : "正常")}
      </div><div class="dashboard-linked-actions" style="margin-top:16px"><button type="button" data-backfill-objects>回填经营对象</button><button type="button" class="secondary" data-clear-runtime>清空演示环境</button><button type="button" class="secondary" data-system-refresh>刷新诊断</button></div></section>
      ${renderBackfillResult(this._backfillResult)}
      <section class="page-section system-section"><div class="section-header"><h3>运行态表计数</h3>${pill(db?.database?.type || "sqlite", "good")}</div><div class="system-layer-list">${renderTableCounts(tableCounts)}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-system-refresh]", "click", () => AppRouter.schedule("system-status-refresh"));
      ctx.delegate("[data-clear-runtime]", "click", async (_, node) => {
        if (!window.confirm("清空演示运行态？会删除导入行、快照、信号、任务、日志、经营商品和经营店铺。")) return;
        node.disabled = true;
        node.textContent = "清空中";
        try {
          const result = await window.AppApi?.resetRuntimeData?.(true);
          this._backfillResult = { status: "runtime_cleared", source: "reset-runtime-data", rowCount: 0, operatingObjectSync: { productUpsertCount: 0, storeUpsertCount: 0 }, after: { visibleCounts: { products: 0, stores: 0 } }, rule: result?.message || "演示运行态已清空。" };
        } catch (error) {
          this._backfillResult = { status: "failed", source: String(error), rowCount: 0, operatingObjectSync: { productUpsertCount: 0, storeUpsertCount: 0 }, after: { visibleCounts: { products: 0, stores: 0 } } };
        }
        AppRouter.schedule("system-clear-runtime");
      });
      ctx.delegate("[data-backfill-objects]", "click", async (_, node) => {
        node.disabled = true;
        node.textContent = "回填中";
        try {
          this._backfillResult = await postJson("/api/system/backfill-operating-objects");
        } catch (error) {
          this._backfillResult = { status: "failed", source: String(error), rowCount: 0, operatingObjectSync: { productUpsertCount: 0, storeUpsertCount: 0 }, after: { visibleCounts: { products: 0, stores: 0 } } };
        }
        AppRouter.schedule("system-backfill");
      });
    },
  };
})();
