(function () {
  let notice = "";
  const s = (value) => AppShell.escape(value);
  function taskButton(item) {
    const task = AppTaskActions.findOpenTask(item);
    return task ? `<button type="button" data-open-task="${s(task.id)}" class="ghost">已在任务清单</button>` : `<button type="button" data-task="${s(item.id)}">加入观察</button>`;
  }
  function row(item) {
    return `<article class="competitor-row"><div class="competitor-title-cell"><div class="competitor-thumb">${s(item.imageLabel)}</div><div class="competitor-title-block"><strong>${s(item.title)}</strong><small>${s(item.id)} · ${s(item.platform)} · ${s(item.store)}</small><span>对应商品：${s(item.targetProduct)}</span></div></div><div class="competitor-metric-strip"><div class="competitor-number-cell"><span>价格</span><strong>${s(item.pricePosition)}</strong><small>不直接跟价</small></div><div class="competitor-number-cell warning"><span>差评</span><strong>${s(item.badReview)}</strong><small>可转测试</small></div><div class="competitor-number-cell ${item.status === "风险" ? "danger" : "good"}"><span>状态</span><strong>${s(item.status)}</strong><small>${s(item.opportunity)}</small></div></div><div class="competitor-actions">${taskButton(item)}</div></article>`;
  }
  window.CompetitorPage = { route: "business-competitors", title: "竞品", render() { return `<section class="competitor-toolbar"><div><p class="eyebrow">COMPETITOR WATCH</p><h2>竞品观察列表</h2><p>竞品只生成观察、复查和测试任务，不直接触发改价。</p></div></section>${notice ? AppShell.notice("操作结果", notice) : ""}<section class="page-section competitor-list-section"><div class="section-header"><h3>竞品列表</h3><span class="status-badge">${AppMockData.competitors.length} 个观察对象</span></div><div class="competitor-card-list">${AppMockData.competitors.map(row).join("")}</div></section>`; }, mount(ctx) { ctx.delegate("[data-open-task]", "click", (_, node) => AppTaskActions.openTodoTask(node.dataset.openTask)); ctx.delegate("[data-task]", "click", async (_, node) => { notice = "任务提交中..."; AppRouter.schedule("competitor-task-start"); const result = await AppTaskActions.createCompetitorTask(node.dataset.task); notice = result?.message || "竞品任务已处理。"; AppRouter.schedule("competitor-task"); }); ctx.addCleanup(AppTaskStore.subscribe(() => AppRouter.schedule("task-store"))); } };
})();
