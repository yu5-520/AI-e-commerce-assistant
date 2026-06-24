(function () {
  const s = (value) => AppShell.escape(value ?? "");

  function ensureAccountCss() {
    if (document.querySelector('link[data-account-ui="1"]')) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/web_demo/account-ui.css?v=10.9.1";
    link.dataset.accountUi = "1";
    document.head.appendChild(link);
  }

  const accountProfile = {
    avatar: "参",
    nickname: "经营参谋账号",
    accountNo: "ACC-ERP-0001",
    phone: "未绑定",
    email: "未绑定",
    status: "启用",
    password: "建议更新",
    twoFactor: "未开启",
    devices: "1 台设备在线",
  };

  const bindings = [
    ["微信", "未绑定", "消息提醒"],
    ["企业微信", "未绑定", "组织通知"],
    ["淘宝商家授权", "未绑定", "店铺数据"],
    ["拼多多商家授权", "未绑定", "店铺数据"],
    ["抖音小店授权", "未绑定", "店铺数据"],
    ["ERP 数据授权", "未绑定", "商品 / 订单 / 库存"],
  ];

  const securityItems = [
    ["登录密码", accountProfile.password, "登录安全"],
    ["手机号", accountProfile.phone, "找回账号"],
    ["邮箱", accountProfile.email, "系统通知"],
    ["二次验证", accountProfile.twoFactor, "企业安全"],
    ["登录设备", accountProfile.devices, "设备管理"],
  ];

  const noticeItems = [
    ["日报提醒", "开启", "经营日报"],
    ["周报提醒", "开启", "复盘报告"],
    ["任务提醒", "开启", "任务流转"],
    ["审计提醒", "开启", "异常复核"],
  ];

  function infoItem(label, value) {
    return `<article><span>${s(label)}</span><strong>${s(value)}</strong></article>`;
  }

  function settingRow([title, status, desc], action = "设置") {
    return `<article class="account-setting-row"><div><strong>${s(title)}</strong><small>${s(desc)}</small></div><span>${s(status)}</span><button type="button" class="secondary" data-account-action data-label="${s(action)}">${s(action)}</button></article>`;
  }

  function actionButton(label, variant = "") {
    return `<button type="button" class="${s(variant)}" data-account-action data-label="${s(label)}">${s(label)}</button>`;
  }

  window.AccountPage = {
    route: "accounts",
    title: "账号",
    async render() {
      ensureAccountCss();
      const payload = await AppApi.accounts();
      const current = payload?.currentUser || {};
      const roleName = current.roleName || "模拟账号";
      const loginName = current.name || "老板";
      return `<section class="account-hero"><div class="account-avatar">${s(accountProfile.avatar)}</div><div class="account-hero-main"><h2>账号中心</h2><p>登录、安全、绑定和通知集中管理。</p></div><div class="account-status-card"><span>当前身份</span><strong>${s(roleName)}</strong><em>${s(accountProfile.status)}</em></div></section>
      <section class="account-grid">
        <article class="account-info-card"><div class="section-header"><h3>基础信息</h3><span class="status-badge">账号</span></div><div class="account-info-list">${[
          ["昵称", accountProfile.nickname],
          ["账号 ID", accountProfile.accountNo],
          ["登录账号", loginName],
          ["当前身份", roleName],
          ["手机号", accountProfile.phone],
          ["邮箱", accountProfile.email],
        ].map(([label, value]) => infoItem(label, value)).join("")}</div></article>
        <article class="account-info-card account-action-card"><div class="section-header"><h3>基础操作</h3><span class="status-badge">操作</span></div><div class="account-action-list">${actionButton("编辑资料")}${actionButton("清除缓存")}${actionButton("退出登录", "secondary")}</div><div class="account-note">真实登录、短信、邮箱和第三方授权在正式版接入。</div></article>
      </section>
      <section class="page-section account-section"><div class="section-header"><h3>安全设置</h3><span class="status-badge">安全</span></div><div class="account-setting-list">${securityItems.map((item) => settingRow(item)).join("")}</div></section>
      <section class="page-section account-section"><div class="section-header"><h3>绑定与授权</h3><span class="status-badge">授权</span></div><div class="account-setting-list">${bindings.map((item) => settingRow(item, "绑定")).join("")}</div></section>
      <section class="page-section account-section"><div class="section-header"><h3>通知设置</h3><span class="status-badge">通知</span></div><div class="account-setting-list">${noticeItems.map((item) => settingRow(item, "调整")).join("")}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-account-action]", "click", (_, node) => {
        const label = node.dataset.label || node.textContent || "设置";
        node.textContent = "暂未接入";
        node.disabled = true;
        window.setTimeout(() => {
          node.disabled = false;
          node.textContent = label;
        }, 900);
      });
    },
  };

  window.RoleConsolePage = {
    route: "role-console",
    title: "权限入口",
    async render() {
      ensureAccountCss();
      return `<section class="report-hero"><div><h2>入口已迁移</h2><p>账号页只保留登录、安全、绑定和通知。权限与店铺归属在系统权限中管理。</p></div><div class="report-hero-side"><strong>兼容入口</strong></div></section><section class="page-section"><div class="section-header"><h3>权限治理</h3><button type="button" data-system-status>进入系统</button></div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-system-status]", "click", () => AppRouter.navigate("system-status"));
    },
  };
})();