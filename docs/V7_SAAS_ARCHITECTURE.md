# V7.4 SaaS 大厂体系架构基底

V7 的目标不是继续堆功能，而是把 V6 的动态经营闭环收束成可交付、可审计、可迁移、可扩展的 SaaS 系统基底。V7.4 在 V7.3 的配置审计、对比和回滚之上，增加发布治理看板：功能开关启用率、灰度覆盖、角色覆盖、审计量和回滚风险都可度量。

## 1. 产品定位

V6 已完成：

```text
报表导入 → 趋势识别 → RAG 指标 → 风险任务 → 权限审批 → 执行回写 → 复盘沉淀
```

V7 完成：

```text
业务闭环 → SaaS 控制面 → 多租户交付 → 组织权限治理 → 标准流程编排 → 审计可观测 → 生产迁移路径
```

V7.1 完成：

```text
SaaS 控制面 → 租户配置 → 功能开关 → 角色可见 → 灰度开放 → 配置审计
```

V7.2 完成：

```text
配置审计能力 → 配置中心前端 → 启用 / 暂停 → 灰度比例 → 角色范围 → 操作审计
```

V7.3 完成：

```text
配置审计记录 → 搜索筛选 → 变更对比 → 回滚配置 → 回滚再审计
```

V7.4 完成：

```text
功能开关 → 灰度规则 → 角色覆盖 → 审计量 → 回滚次数 → 发布状态看板
```

一句话定义：

```text
V7.4 是 AI 电商经营系统的 SaaS 发布治理版本。
```

## 2. V7.4 十层控制面

1. 租户与组织控制面：tenant / org / store / user / role / data scope。
2. 数据接入与契约中心：ERP、CRM、平台报表统一入口，后台字段识别与商品匹配。
3. 经营趋势与信号中心：商品快照、指标趋势、经营信号、平台/类目/店铺趋势。
4. RAG 指标与规则中心：库存安全线、ROI、CTR、CVR、毛利、售后红线和案例记忆。
5. 风险门控与任务编排中心：低/中/高风险分级，高风险趋势门控，任务生命周期。
6. 权限额度与审批中心：运营申请、总管审批、老板审批、额度校验和审批事件。
7. 执行回写与复盘中心：执行结果、实际花费、采购金额、证据、复盘案例和 RAG 沉淀。
8. 审计、日志与可观测中心：业务审计、技术日志、worker、LLM gateway、数据版本、回滚记录。
9. SaaS 交付治理中心：版本、租户配置、功能开关、灰度、发布看板、运行模式、SLA 检查。
10. 租户配置与功能开关中心：tenant config、feature flag、rollout、role gating、config audit、console actions、compare、rollback、release dashboard。

## 3. 主业务流程

```text
报表/API/RPA 数据接入
→ 字段识别与商品匹配
→ 商品快照与指标趋势
→ 经营信号聚合
→ RAG 指标约束
→ 风险分级任务
→ 权限额度与审批生命周期
→ 执行任务与结果回写
→ 执行复盘与 RAG 案例沉淀
→ 租户配置中心前端操作
→ 配置审计、对比、回滚
→ 发布治理看板与交付观测
```

## 4. SaaS 必须守住的边界

- 所有业务动作必须归属到租户、组织、店铺、角色和数据范围。
- 所有中高风险任务必须经过 RAG 指标、历史趋势、权限额度和审批链路。
- Agent 不能自造指标，不能绕过审批，不能直接执行高风险动作。
- 审批和执行必须分离。
- 执行回写只记录实际结果和证据，不自动改写经营数据。
- RAG 沉淀只保存案例，不自动改写公司规则。
- 所有关键动作必须可审计、可回滚、可追踪。
- SaaS 能力必须经过租户配置、角色权限和灰度规则开放，不能硬编码成全租户可用。
- 功能开关前端操作必须限制在老板 / 总管，灰度规则只允许老板操作。
- 配置回滚必须以审计记录为依据，且回滚动作本身必须再次写入审计。
- 发布状态必须可度量，不能只看“开关是否打开”。

## 5. V7.4 发布治理能力

发布治理看板聚合：

```text
featureCount
→ enabledCount
→ rolloutRuleCount
→ enabledForContextCount
→ statusCounts
→ stageCounts
→ roleCoverage
→ rollbackCount
```

单个功能开关的发布状态：

```text
paused
full_release
gray_release
rollback_watch
enabled_without_rollout
```

## 6. 当前 V7.4 实现入口

```text
GET  /api/architecture/v7
GET  /api/architecture/v7/tenant-config
POST /api/architecture/v7/feature-flags/{flag_key}
POST /api/architecture/v7/feature-flags/{flag_key}/rollout
GET  /api/architecture/v7/config-audits
GET  /api/architecture/v7/config-audits/{audit_id}/compare
POST /api/architecture/v7/config-audits/{audit_id}/rollback
GET  /api/architecture/v7/release-governance
```

前端入口：

```text
配置中心
配置审计
发布治理
```

## 7. 验收标准

V7.4 完成后，系统至少能回答：

- 当前账号属于哪个租户、组织、店铺和角色？
- 当前租户启用了哪些模块和功能？
- 当前角色可见哪些功能开关？
- 当前功能是否命中灰度规则？
- 当前功能为什么可用或不可用？
- 配置变更是否进入审计？
- 某次配置变更和上一版差异是什么？
- 是否可以按审计记录回滚，并留下回滚记录？
- 每个功能是暂停、灰度、全量还是回滚观察？
- 当前功能发布覆盖了哪些角色、多少灰度比例、发生过几次回滚？
