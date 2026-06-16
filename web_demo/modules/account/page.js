(function () {
  const s = (value) => AppShell.escape(value);

  const accountProfile = {
    avatar: "参",
    nickname: "经营参谋账号",
    accountNo: "ACC-ERP-0001",
    phone: "未绑定",
    email: "未绑定",
    status: "启用",
    password: "建议定期更新",
    twoFactor: "未开启",
    devices: "1 台设备在线",
  };

  const bindings = [
    ["微信", "未绑定", "用于消息提醒和快捷登录"],
    ["企业微信", "未绑定", "用于组织通知和日报推送"],
    ["淘宝商家授权", "未绑定", "仅显示绑定状态，不控制店铺权限"],
    ["拼多多商家授权", "未绑定", "仅显示绑定状态，不控制店铺权限"],
    ["抖音小店授权", "未绑定", "仅显示绑定状态，不控制店铺权限"],
    ["ERP 数据授权", "未绑定", "后续接入商品、订单、库存数据"],
  ];

  const securityItems = [
    ["修改密码", accountProfile.password, "用于登录安全"],
    ["绑定手机号", accountProfile.phone, "用于找回账号和安全验证"],
    ["绑定邮箱", accountProfile.email, "用于接收系统通知"],
    ["二次验证", accountProfile.twoFactor, "建议企业版开启"],
    ["登录设备", accountProfile.devices, "查看最近登录设备"],
  ];

  const noticeItems = [
    ["日报提醒", "开启", "每天收经营日报"],
    ["周报提醒", "开启", "每周收复盘报告"],
    ["任务提醒", "开启", "任务流转时提醒"],
    ["审计提醒", "开启", "复盘审计异常提醒"],
  ];

  function settingRow([title, status, desc], action = "设置") {
    return `<article class="account-setting-row"><div><strong>${s(title)}</strong><small>${s(desc)}</small></div><span>${s(status)}</span><button type="button" class="secondary" data-account-action>${s(action)}</button></article>`;
  }

  window.AccountPage = {
    route: "accounts",
    title: "账号中心",
    async render() {
      const payload = await AppApi.accounts();
      const current = payload?.currentUser || {};
      return `<section class="account-hero"><div class="account-avatar">${s(accountProfile.avatar)}</div><div><p class="eyebrow">ACCOUNT CENTER · V2.3.7</p><h2>账号中心</h2><p>这里处理登录、安全、绑定和通知。组织关系、岗位权限、店铺授权统一放在「组织效率」。</p></div><div class="account-status"><span>账号状态</span><strong>${s(accountProfile.status)}</strong></div></section>
      <section class="account-grid">
        <article class="account-info-card"><h3>基础信息</h3><div class="account-info-list"><div><span>昵称</span><strong>${s(accountProfile.nickname)}</strong></div><div><span>账号 ID</span><strong>${s(accountProfile.accountNo)}</strong></div><div><span>当前登录身份</span><strong>${s(current.roleName || "模拟账号")}</strong></div><div><span>登录账号</span><strong>${s(current.name || "老板")}</strong></div><div><span>手机号</span><strong>${s(accountProfile.phone)}</strong></div><div><span>邮箱</span><strong>${s(accountProfile.email)}</strong></div></div></article>
        <article class="account-info-card"><h3>基础操作</h3><div class="account-action-list"><button type="button" data-account-action>编辑资料</button><button type="button" data-account-action>清除本地缓存</button><button type="button" class="secondary" data-account-action>退出登录</button></div><p>当前为 MVP 模拟账号，真实版本再接登录、密码、短信、邮箱和第三方授权。</p></article>
      </section>
      <section class="page-section account-section"><div class="section-header"><h3>安全设置</h3><span class="status-badge">SECURITY</span></div><div class="account-setting-list">${securityItems.map((item) => settingRow(item)).join("")}</div></section>
      <section class="page-section account-section"><div class="section-header"><h3>绑定与授权</h3><span class="status-badge">BINDING</span></div><div class="account-setting-list">${bindings.map((item) => settingRow(item, "绑定")).join("")}</div></section>
      <section class="page-section account-section"><div class="section-header"><h3>通知设置</h3><span class="status-badge">NOTICE</span></div><div class="account-setting-list">${noticeItems.map((item) => settingRow(item, "调整")).join("")}</div></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-account-action]", "click", (_, node) => {
        node.textContent = "暂未接入";
        node.disabled = true;
        window.setTimeout(() => {
          node.disabled = false;
          node.textContent = node.classList.contains("secondary") ? "设置" : "设置";
        }, 900);
      });
    },
  };

  window.RoleConsolePage = {
    route: "role-console",
    title: "角色权限控制台",
    async render() {
      return `<section class="report-hero"><div><p class="eyebrow">ROLE CONSOLE · LEGACY</p><h2>入口已迁移</h2><p>账号页只保留登录、安全、绑定和通知设置。组织结构、职位关系、店铺范围和权限模板请进入「组织效率」。</p></div><div class="report-hero-side"><span>当前入口</span><strong>兼容保留</strong><small>建议使用组织效率</small></div></section><section class="page-section"><div class="section-header"><h3>组织权限治理</h3><button type="button" data-org-efficiency>进入组织效率</button></div><p>这里不再作为日常权限管理页面，仅保留给旧路由兼容。</p></section>`;
    },
    mount(ctx) {
      ctx.delegate("[data-org-efficiency]", "click", () => AppRouter.navigate("org-efficiency"));
    },
  };
})();
