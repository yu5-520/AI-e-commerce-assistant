(function () {
  const s = (value) => AppShell.escape(value);

  const stores = [
    { platform: "淘宝", name: "家居生活主店", products: 126, orders: 236, sales: 42800, profit: 9100, comments: 18320, refund: "3.2%", stock: 186000, status: "稳定" },
    { platform: "拼多多", name: "家居百货店", products: 98, orders: 318, sales: 35600, profit: 6200, comments: 24680, refund: "5.8%", stock: 142000, status: "关注" },
    { platform: "抖音小店", name: "家居好物号", products: 64, orders: 152, sales: 29800, profit: 4800, comments: 10560, refund: "6.1%", stock: 98000, status: "关注" },
  ];

  const people = [
    { name: "店群总管", role: "总管", state: "待派发", current: 3, done: 0, returned: 0, avg: "12 分", load: 72, action: "6 分钟前查看任务池" },
    { name: "运营 A", role: "运营", state: "处理中", current: 2, done: 4, returned: 1, avg: "18 分", load: 64, action: "3 分钟前提交处理结果" },
    { name: "运营 B", role: "运营", state: "空闲", current: 0, done: 2, returned: 0, avg: "21 分", load: 28, action: "28 分钟前完成任务" },
    { name: "数据财务", role: "财务", state: "在线", current: 1, done: 3, returned: 0, avg: "15 分", load: 45, action: "9 分钟前补充财务口径" },
  ];

  const supply = [
    { name: "义乌家居源头仓", kind: "收纳", cost: "+2.8%", cycle: "3 天", stock: 186000, safe: "正常", state: "稳定" },
    { name: "佛山办公坐垫厂", kind: "坐垫", cost: "+6.4%", cycle: "5 天", stock: 142000, safe: "偏低", state: "关注" },
    { name: "台州塑料家居厂", kind: "收纳盒", cost: "-1.2%", cycle: "4 天", stock: 98000, safe: "正常", state: "稳定" },
  ];

  const traffic = [
    { platform: "淘宝", spend: 12800, roas: 2.9, cpc: "¥0.82", cv: "4.8%", paid: 86, natural: 150, state: "稳定" },
    { platform: "拼多多", spend: 9600, roas: 2.2, cpc: "¥0.64", cv: "5.6%", paid: 128, natural: 190, state: "关注" },
    { platform: "抖音小店", spend: 15200, roas: 1.8, cpc: "¥1.12", cv: "3.9%", paid: 74, natural: 78, state: "关注" },
  ];

  const finance = { sales: 108200, gross: 20100, ad: 37600, refund: 7200, logistics: 9600, fee: 4100, inventory: 426000, net: 6800 };

  const retrospectives = [
    {
      type: "日报",
      period: "今日",
      owner: "店群总管",
      scope: "全部店群",
      target: "日销 100,000",
      actual: "108,200",
      rate: "108.2%",
      issue: "抖音 ROAS 偏低，拼多多退款率抬升",
      status: "已接收",
      action: "纳入周复盘观察",
      details: ["抖音小店 ROAS 1.8，低于目标 2.5。", "拼多多退款率 5.8%，高于店群均值。", "今日销售达标，但利润被投流和退款吃掉。"],
      agentPlan: ["检索今日投流消耗、退款订单和差评商品。", "判断异常是否连续出现。", "如果连续 3 天未改善，自动进入周复盘审计。"],
    },
    {
      type: "周报",
      period: "本周",
      owner: "店群总管",
      scope: "家居生活店群",
      target: "周销 800,000",
      actual: "725,000",
      rate: "90.6%",
      issue: "低效投流持续 3 天，部分商品差评未压住",
      status: "未达标",
      action: "生成下周经营任务",
      details: ["周销达成率 90.6%，未达到目标。", "抖音低 ROAS 商品持续消耗预算。", "拼多多差评商品未形成完整复查闭环。"],
      agentPlan: ["检索本周订单、广告消耗、退款、差评和任务完成记录。", "判断未达标是流量效率问题、商品问题还是组织处理延迟。", "输出下周经营任务草案。"],
    },
    {
      type: "月报",
      period: "本月",
      owner: "数据财务",
      scope: "全部平台",
      target: "净利率 8%",
      actual: "6.3%",
      rate: "78.8%",
      issue: "广告费和库存资金占用偏高",
      status: "审计中",
      action: "生成月度降本任务",
      details: ["净利率未达标，广告费和库存资金占用偏高。", "部分供应商成本上浮，库存周转需要继续观察。", "月度任务需要同时压投流、降库存、控退款。"],
      agentPlan: ["检索月度利润表、供应商成本、库存周转和平台扣点。", "判断现金流压力来源。", "生成下月降本增效任务。"],
    },
    {
      type: "专项复盘",
      period: "618 后复盘",
      owner: "运营 A",
      scope: "抖音小店",
      target: "ROI 2.5",
      actual: "1.8",
      rate: "72.0%",
      issue: "高消耗低转化商品未及时停投",
      status: "需整改",
      action: "下发投流复查",
      details: ["抖音低转化商品消耗过高。", "预算收缩动作不够及时。", "需要形成投流阈值和停投规则。"],
      agentPlan: ["检索商品广告消耗、点击率、转化率和订单利润。", "判断哪些商品需要停投、降预算或换素材。", "形成投流复查任务草案。"],
    },
  ];

  const auditIssues = [
    { issue: "周报目标未达标", source: "本周周报", level: "高", owner: "店群总管", reason: "周销达成率 90.6%", action: "下周目标拆解", status: "待处理", evidence: ["本周目标 800,000，实际 725,000。", "抖音投流效率下降，拼多多退款率上升。"], agentChecks: ["检查目标拆解是否落到店铺和运营。", "检查是否已有任务处理低效投流。"] },
    { issue: "投流 ROI 不达标", source: "专项复盘", level: "高", owner: "运营 A", reason: "抖音 ROAS 1.8，低于目标 2.5", action: "降低低转化预算", status: "待处理", evidence: ["抖音 ROAS 连续低于目标。", "高消耗商品未及时停投。"], agentChecks: ["检索商品级广告消耗。", "判断停投清单和降预算比例。"] },
    { issue: "退款率上升", source: "日报", level: "中", owner: "运营 B", reason: "拼多多退款率 5.8%", action: "复查差评商品", status: "待处理", evidence: ["退款率高于店群均值。", "差评商品集中在家居百货店。"], agentChecks: ["检索退款原因。", "检查差评商品是否已有处理任务。"] },
    { issue: "复核延迟", source: "任务池", level: "中", owner: "店群总管", reason: "2 条任务接近超时", action: "优化复核节奏", status: "待处理", evidence: ["任务池存在接近超时任务。", "复核节点可能成为闭环卡点。"], agentChecks: ["检索任务创建、提交、复核时间线。", "判断是否需要调整主管复核节奏。"] },
  ];

  const nextTasks = [
    { cycle: "下周", task: "抖音低 ROAS 商品预算收缩", owner: "店群总管", split: ["运营 A 复查低 ROAS 商品。", "数据财务复核 ROI 和广告消耗。", "店群总管确认停投 / 降预算清单。"], priority: "高", status: "待下发", source: "本周周报 + 专项复盘", goal: "降低低效投流消耗，提高下周 ROAS。" },
    { cycle: "下周", task: "拼多多退款率商品专项复查", owner: "店群总管", split: ["运营 B 处理差评和退货原因。", "总管复核商品页、客服话术和物流问题。", "形成退款率周内压降目标。"], priority: "中", status: "待下发", source: "日报 + 周报", goal: "降低退款率，减少售后吞利。" },
    { cycle: "下月", task: "库存资金占用降至 380,000 以下", owner: "数据财务", split: ["供应商补货节奏复查。", "滞销库存清理。", "月度现金流压力复核。"], priority: "高", status: "待确认", source: "月报", goal: "降低库存占用，释放现金流。" },
  ];

  const tasks = () => window.AppTaskStore?.listActiveTasks?.() || [];
  const logs = () => window.AppTaskStore?.listLogs?.() || [];
  const money = (v) => `¥${Number(v || 0).toLocaleString("zh-CN")}`;
  const total = (arr, key) => arr.reduce((n, x) => n + Number(x[key] || 0), 0);
  const statusClass = (v) => ["稳定", "在线", "已接收"].includes(v) ? "good" : ["空闲", "审计中", "待确认"].includes(v) ? "watch" : "warning";
  const hero = (code, title, desc, label, value) => `<section class="report-hero realtime-hero"><div><p class="eyebrow">${s(code)}</p><h2>${s(title)}</h2><p>${s(desc)}</p></div><div class="report-hero-side"><span>${s(label)}</span><strong>${s(value)}</strong><small>老板统筹层</small></div></section>`;
  const metrics = (items) => `<section class="kpi-grid report-metrics realtime-metrics">${items.map(([a, b, c]) => `<article class="card realtime-metric"><h3>${s(a)}</h3><strong>${s(b)}</strong><small>${s(c)}</small></article>`).join("")}</section>`;
  const pills = (items) => `<div class="review-pill-row">${items.map((item) => `<span>${s(item)}</span>`).join("")}</div>`;
  const detailList = (title, items) => `<div class="review-detail-block"><strong>${s(title)}</strong><ul>${items.map((item) => `<li>${s(item)}</li>`).join("")}</ul></div>`;
  const cards = (title, badge, items) => `<section class="page-section realtime-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">${s(badge)}</span></div><div class="supply-grid">${items.map((x) => `<article class="chain-card"><header><div><span class="status-dot ${statusClass(x.state || x.status)}"></span><strong>${s(x.title)}</strong></div><span class="status-badge">${s(x.badge)}</span></header><p>${s(x.text)}</p><footer>${s(x.footer || x.state || x.status || "同步")}</footer></article>`).join("")}</div></section>`;
  const table = (title, head, rows) => `<section class="page-section realtime-section"><div class="section-header"><h3>${s(title)}</h3><span class="status-badge">TABLE</span></div><div class="store-table"><div class="finance-table-row head">${head.map((x) => `<span>${s(x)}</span>`).join("")}</div>${rows.map((row) => `<div class="finance-table-row">${row.map((x, i) => i ? `<span>${s(x)}</span>` : `<strong>${s(x)}</strong>`).join("")}</div>`).join("")}</div></section>`;

  function storeNames(user, storeList) {
    const map = new Map((storeList || []).map((item) => [item.id, item.name]));
    return (user.storeIds || []).map((id) => map.get(id) || id).join(" / ") || "未授权店铺";
  }

  function orgTree(account) {
    const users = account?.users || [];
    const storeList = account?.stores || [];
    const owner = users.find((u) => u.roleId === "owner") || users[0] || {};
    const manager = users.find((u) => u.roleId === "manager") || {};
    const children = users.filter((u) => ["operator", "finance", "observer"].includes(u.roleId));
    return `<section class="page-section org-section"><div class="section-header"><h3>职位关系网</h3><span class="status-badge">ORG MAP</span></div><div class="org-map"><article class="org-node owner"><strong>${s(owner.name || "老板")}</strong><span>${s(owner.roleName || "老板账号")}</span><small>全部店群 / 组织权限最终负责人</small></article><div class="org-line"></div><article class="org-node manager"><strong>${s(manager.name || "店群总管")}</strong><span>${s(manager.roleName || "店群总管账号")}</span><small>主管：${s(owner.name || "老板")} · ${s(storeNames(manager, storeList))}</small></article><div class="org-children">${children.map((user) => `<article class="org-node"><strong>${s(user.name)}</strong><span>${s(user.roleName)}</span><small>直属主管：${s(manager.name || "店群总管")} · ${s(storeNames(user, storeList))}</small></article>`).join("")}</div></div></section>`;
  }

  function orgControls(account) {
    if (!AppApi.can("manage_roles")) return `<section class="page-section"><h3>账号权限控制</h3><p>当前账号只有查看权限，不能调整角色、店铺范围或权限模板。</p></section>`;
    const roles = account?.roles || [];
    const users = account?.users || [];
    const storeList = account?.stores || [];
    const permissions = account?.permissions || [];
    const userCards = users.map((user) => `<article class="org-control-card"><div class="section-header"><h3>${s(user.name)}</h3><span class="status-badge">${s(user.roleName)}</span></div><p>负责店铺：${s(storeNames(user, storeList))}</p><div class="permission-chip-row">${roles.map((role) => `<button type="button" class="secondary" data-role-change="${s(user.id)}:${s(role.id)}">${s(role.name)}</button>`).join("")}</div><div class="permission-chip-row">${storeList.map((store) => `<button type="button" class="secondary" data-store-toggle="${s(user.id)}:${s(store.id)}">${(user.storeIds || []).includes(store.id) ? "✓ " : ""}${s(store.name)}</button>`).join("")}</div></article>`).join("");
    const roleCards = roles.map((role) => { const selected = new Set(role.permissions || []); return `<article class="org-control-card"><div class="section-header"><h3>${s(role.name)}</h3><span class="status-badge">权限模板</span></div><div class="permission-chip-row">${permissions.map((permission) => `<button type="button" class="secondary" data-permission="${s(role.id)}:${s(permission.id)}">${selected.has(permission.id) ? "✓ " : ""}${s(permission.name)}</button>`).join("")}</div></article>`; }).join("");
    return `<section class="page-section org-section"><div class="section-header"><h3>人员账号权限控制</h3><span class="status-badge">CONTROL</span></div><div class="org-control-grid">${userCards}</div></section><section class="page-section org-section"><div class="section-header"><h3>角色权限模板</h3><span class="status-badge">RBAC</span></div><div class="org-control-grid">${roleCards}</div></section>`;
  }

  function orgAlerts(account) {
    const users = account?.users || [];
    const unassigned = users.filter((u) => !u.storeIds?.length).length;
    return cards("组织配置观察", "GOVERNANCE", [
      { title: "主管链路", badge: "正常", state: "稳定", text: "老板 → 店群总管 → 运营 / 财务 / 观察者，当前没有空挂主管链路。" },
      { title: "店铺授权", badge: unassigned ? "关注" : "正常", state: unassigned ? "关注" : "稳定", text: unassigned ? `${unassigned} 个账号没有绑定店铺范围，需要补齐。` : "所有执行账号都已绑定可见店铺范围。" },
      { title: "权限审计", badge: "需记录", state: "关注", text: "角色升降级、店铺授权、权限模板调整会进入复盘审计，用于后续追溯。" },
    ]);
  }

  function retrospectivePanels() {
    const rows = retrospectives.map((item) => `<details class="review-card"><summary><div><span class="status-dot ${statusClass(item.status)}"></span><strong>${s(item.type)} · ${s(item.period)}</strong><small>${s(item.owner)} · ${s(item.scope)}</small></div><div class="review-summary-meta"><span>${s(item.status)}</span><b>${s(item.rate)}</b></div></summary><div class="review-detail">${pills([`目标 ${item.target}`, `实际 ${item.actual}`, `达成率 ${item.rate}`, item.action])}<div class="review-detail-note">${s(item.issue)}</div>${detailList("复盘要点", item.details)}${detailList("Agent 预留判断", item.agentPlan)}</div></details>`).join("");
    return `<section class="page-section review-section"><div class="section-header"><h3>周期复盘接收</h3><span class="status-badge">可展开</span></div><div class="review-card-list">${rows}</div></section>`;
  }

  function auditPanels() {
    const rows = auditIssues.map((item) => `<details class="review-card"><summary><div><span class="status-dot ${statusClass(item.status)}"></span><strong>${s(item.issue)}</strong><small>${s(item.source)} · 负责人：${s(item.owner)}</small></div><div class="review-summary-meta"><span>${s(item.level)}</span><b>${s(item.status)}</b></div></summary><div class="review-detail">${pills([item.reason, item.action, `等级 ${item.level}`])}${detailList("审计证据", item.evidence)}${detailList("Agent 判断项", item.agentChecks)}</div></details>`).join("");
    return `<section class="page-section review-section"><div class="section-header"><h3>审计问题清单</h3><span class="status-badge">可展开</span></div><div class="review-card-list">${rows}</div></section>`;
  }

  function taskDraftPanels() {
    const rows = nextTasks.map((item) => `<details class="review-card"><summary><div><span class="status-dot ${statusClass(item.status)}"></span><strong>${s(item.cycle)} · ${s(item.task)}</strong><small>${s(item.source)} · 责任主管：${s(item.owner)}</small></div><div class="review-summary-meta"><span>${s(item.priority)}</span><b>${s(item.status)}</b></div></summary><div class="review-detail">${pills([item.goal, `优先级 ${item.priority}`, item.status])}${detailList("拆分方向", item.split)}<div class="review-action-row"><button type="button">生成任务</button><button type="button" class="secondary">下发给总管</button><button type="button" class="secondary">进入待办</button></div></div></details>`).join("");
    return `<section class="page-section review-section"><div class="section-header"><h3>下周期任务草案</h3><span class="status-badge">可展开</span></div><div class="review-card-list">${rows}</div></section>`;
  }

  window.StoreOverviewPage = { route: "store-overview", title: "店群总览", render() { return `${hero("STORE GROUP LIVE BOARD", "店群总览", "老板先看平台、店铺、商品、订单、销售额、利润、评论、退款、库存和待办。", "运营店铺", stores.length)}${metrics([["运营平台", 3, "淘宝 / 拼多多 / 抖音"], ["店铺数量", stores.length, "当前运营中"], ["今日订单", total(stores, "orders"), "实时经营"], ["销售额", money(total(stores, "sales")), "跨平台汇总"], ["利润", money(total(stores, "profit")), "预估毛利"], ["评论", total(stores, "comments").toLocaleString("zh-CN"), "口碑资产"], ["库存金额", money(total(stores, "stock")), "资金占用"], ["待办", tasks().length, "进入闭环"]])}${cards("平台经营", "LIVE", stores.map(x => ({ title: x.platform, badge: x.status, state: x.status, text: `${x.name} · 商品 ${x.products} · 订单 ${x.orders} · 销售额 ${money(x.sales)} · 利润 ${money(x.profit)}` })))}${table("店铺经营明细", ["店铺", "平台", "商品", "订单", "销售额", "利润", "评论", "退款率"], stores.map(x => [x.name, x.platform, x.products, x.orders, money(x.sales), money(x.profit), x.comments, x.refund]))}`; } };

  window.TaskCommandPage = { route: "task-command", title: "人员总览", render() { return `${hero("PEOPLE OVERVIEW", "人员总览", "老板看任务压在谁身上、谁忙、谁空闲、谁被退回、谁可能成为闭环卡点。", "在线人员", people.length)}${metrics([["在线人员", people.length, "总管 / 运营 / 财务"], ["忙碌人员", people.filter(x => x.load >= 60).length, "关注负荷"], ["空闲人员", people.filter(x => x.state === "空闲").length, "可承接任务"], ["今日完成", total(people, "done"), "团队产出"], ["退回", total(people, "returned"), "质量观察"], ["平均处理", "16 分", "团队均值"], ["待派发", 3, "总管处理"], ["任务池", tasks().length, "待闭环"]])}${cards("员工实时状态", "LIVE", people.map(x => ({ title: x.name, badge: x.state, state: x.state, text: `${x.role} · 当前 ${x.current} · 完成 ${x.done} · 退回 ${x.returned} · 负荷 ${x.load}% · ${x.action}` })))}${table("人员任务映射", ["人员", "角色", "状态", "当前", "完成", "退回", "平均", "负荷"], people.map(x => [x.name, x.role, x.state, x.current, x.done, x.returned, x.avg, `${x.load}%`]))}`; } };

  window.ProfitBudgetPage = { route: "profit-budget", title: "供投财务", render() { return `${hero("SUPPLY · TRAFFIC · FINANCE", "供投财务", "老板在这里看货、流量、钱三条链路：供货是否稳定、投流是否划算、财务结果是否健康。", "净利润", money(finance.net))}${metrics([["供应商", supply.length, "核心供货"], ["库存金额", money(total(supply, "stock")), "供货资金"], ["供货周期", "4 天", "平均周期"], ["广告消耗", money(total(traffic, "spend")), "今日投放"], ["综合 ROAS", "2.2", "付费回收"], ["毛利", money(finance.gross), "今日汇总"], ["退款成本", money(finance.refund), "售后吞利"], ["现金压力", "中", "库存 + 投放"]])}${cards("货 · 流量 · 钱", "CHAIN", [{ title: "供货", badge: `${supply.length} 家`, state: "关注", text: `库存 ${money(total(supply, "stock"))} · 平均供货 4 天 · 1 家成本上浮` }, { title: "投放", badge: `${traffic.length} 平台`, state: "关注", text: `消耗 ${money(total(traffic, "spend"))} · ROAS 2.2 · 低效消耗需关注` }, { title: "财务", badge: "今日", state: "稳定", text: `销售额 ${money(finance.sales)} · 毛利 ${money(finance.gross)} · 净利润 ${money(finance.net)}` }])}${table("供应链看板", ["供应商", "品类", "成本变化", "供货周期", "库存", "安全库存", "状态", ""], supply.map(x => [x.name, x.kind, x.cost, x.cycle, money(x.stock), x.safe, x.state, ""]))}${table("投流看板", ["平台", "消耗", "ROAS", "点击成本", "转化率", "付费订单", "自然订单", "状态"], traffic.map(x => [x.platform, money(x.spend), x.roas, x.cpc, x.cv, x.paid, x.natural, x.state]))}${table("财务汇总", ["销售额", "毛利", "广告费", "退款", "物流", "扣点", "库存资金", "净利润"], [[money(finance.sales), money(finance.gross), money(finance.ad), money(finance.refund), money(finance.logistics), money(finance.fee), money(finance.inventory), money(finance.net)]])}`; } };

  window.OrgEfficiencyPage = { route: "org-efficiency", title: "组织效率", async render() { const account = await AppApi.accounts(); const users = account?.users || []; return `${hero("ORG PERMISSION NETWORK", "组织效率", "这里看组织结构、职位关系、账号权限、店铺授权和角色模板。账号页只回答我是谁，组织效率回答组织怎么运转。", "员工总数", users.length)}${metrics([["员工总数", users.length, "全部账号"], ["主管人数", users.filter(x => x.roleId === "manager").length, "管理层"], ["运营人数", users.filter(x => x.roleId === "operator").length, "执行层"], ["财务人数", users.filter(x => x.roleId === "finance").length, "数据财务"], ["只读账号", users.filter(x => x.roleId === "observer").length, "观察权限"], ["权限异常", 0, "Mock 检查"], ["空挂人员", users.filter(x => !x.storeIds?.length).length, "未绑定店铺"], ["权限变更", (account?.roleChangeLogs || []).length, "审计记录"]])}${orgTree(account)}${orgControls(account)}${orgAlerts(account)}`; }, mount(ctx) { ctx.delegate("[data-role-change]", "click", async (_, node) => { const [userId, roleId] = node.dataset.roleChange.split(":"); await AppApi.updateUserRole(userId, roleId); await AppApi.prefetch(); AppRouter.schedule("org-role-change"); }); ctx.delegate("[data-store-toggle]", "click", async (_, node) => { const [userId, storeId] = node.dataset.storeToggle.split(":"); const account = await AppApi.accounts(); const user = (account.users || []).find((item) => item.id === userId); const current = new Set(user?.storeIds || []); current.has(storeId) ? current.delete(storeId) : current.add(storeId); await AppApi.updateUserStores(userId, Array.from(current)); await AppApi.prefetch(); AppRouter.schedule("org-store-toggle"); }); ctx.delegate("[data-permission]", "click", async (_, node) => { const [roleId, permissionId] = node.dataset.permission.split(":"); const account = await AppApi.accounts(); const role = (account.roles || []).find((item) => item.id === roleId); const current = new Set(role?.permissions || []); current.has(permissionId) ? current.delete(permissionId) : current.add(permissionId); await AppApi.updateRolePermissions(roleId, Array.from(current)); await AppApi.prefetch(); AppRouter.schedule("org-permission-toggle"); }); } };

  window.ReviewAuditPage = { route: "review-audit", title: "复盘审计", render() { return `${hero("RETROSPECTIVE AUDIT", "复盘审计", "这里接收日报、周报、月报和专项复盘，审查任务超时、目标未达标、业绩未达标、ROI 不达标等运行失误点，并形成下周 / 下月任务草案。", "待生成任务", nextTasks.length)}${metrics([["今日日报", 1, "已接收"], ["本周周报", 1, "未达标"], ["本月月报", 1, "审计中"], ["未提交复盘", 0, "当前周期"], ["未达标项目", retrospectives.filter(x => x.status !== "已接收").length, "需审查"], ["任务超时", 2, "运行失误"], ["审计异常", auditIssues.length, "待处理"], ["待生成任务", nextTasks.length, "下周期"]])}${retrospectivePanels()}${auditPanels()}${taskDraftPanels()}`; } };
})();
