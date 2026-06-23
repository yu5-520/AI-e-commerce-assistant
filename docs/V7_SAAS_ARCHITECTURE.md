# V7.1 SaaS 大厂体系架构基底

V7 的目标不是继续堆功能，而是把 V6 的动态经营闭环收束成可交付、可审计、可迁移、可扩展的 SaaS 系统基底。V7.1 在 V7 控制面之上增加租户配置中心、功能开关和灰度规则，让系统具备按租户、角色、版本逐步开放能力的 SaaS 交付边界。

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
SaaS 控制面 → 租户配置 → 功能开关 → 角色可见 → 灰度开放 → 审计回滚
```

一句话定义：

```text
V7.1 是 AI 电商经营系统的 SaaS 配置治理版本。
```

## 2. V7.1 十层控制面

1. 租户与组织控制面：tenant / org / store / user / role / data scope。
2. 数据接入与契约中心：ERP、CRM、平台报表统一入口，后台字段识别与商品匹配。
3. 经营趋势与信号中心：商品快照、指标趋势、经营信号、平台/类目/店铺趋势。
4. RAG 指标与规则中心：库存安全线、ROI、CTR、CVR、毛利、售后红线和案例记忆。
5. 风险门控与任务编排中心：低/中/高风险分级，高风险趋势门控，任务生命周期。
6. 权限额度与审批中心：运营申请、总管审批、老板审批、额度校验和审批事件。
7. 执行回写与复盘中心：执行结果、实际花费、采购金额、证据、复盘案例和 RAG 沉淀。
8. 审计、日志与可观测中心：业务审计、技术日志、worker、LLM gateway、数据版本、回滚记录。
9. SaaS 交付治理中心：版本、租户配置、功能开关、灰度、运行模式、SLA 检查。
10. 租户配置与功能开关中心：tenant config、feature flag、rollout、role gating、config audit。

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
→ 租户配置、功能开关、灰度与交付治理
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

## 5. V7.1 配置中心数据结构

```text
tenant_configs_v7
feature_flags_v7
feature_rollout_rules_v7
tenant_config_audit_v7
```

功能开关的判断顺序：

```text
feature enabled
→ allowed roles
→ tenant / org rollout rule
→ rollout percentage
→ enabledForContext
```

## 6. 生产化迁移路径

V7.1 当前仍允许 SQLite demo runtime，但架构边界按 SaaS 设计：

```text
SQLite demo runtime
→ Repository mirror
→ PostgreSQL primary-write
→ queue / worker scale-out
→ tenant config / feature flag
→ rollout / audit / rollback
→ observability / SLA
→ SaaS deployment
```

## 7. 验收标准

V7.1 完成后，系统至少能回答：

- 当前账号属于哪个租户、组织、店铺和角色？
- 当前租户启用了哪些模块和功能？
- 当前角色可见哪些功能开关？
- 当前功能是否命中灰度规则？
- 当前功能为什么可用或不可用？
- 当前数据来源、版本、字段识别和业务投影是什么？
- 当前任务为什么生成，风险等级是什么？
- 当前账号是否有额度，审批链路是谁？
- 执行结果是多少，证据是什么？
- 复盘是否进入 RAG 案例记忆？

## 8. 当前 V7.1 实现入口

```text
GET  /api/architecture/v7
GET  /api/architecture/v7/tenant-config
POST /api/architecture/v7/feature-flags/{flag_key}
```

`/api/architecture/v7` 返回 SaaS 控制面、流程注册表、治理检查项、当前账号数据范围计划和 V7.1 租户配置摘要。
