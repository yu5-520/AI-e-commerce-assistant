# 模块边界

## 1. 当前边界目标

本文件只描述 v4.1.0 当前 active trunk 的模块边界。

当前产品是：

```text
AI ERP 经营单元协同工作台 + 模块 Agent 增强层 + RAG-ready 运营经验记忆层
```

当前产品不是：

```text
完整 ERP
完整 CRM
真实企业 SSO
自动运营 Agent
真实店铺后台操作系统
无审核知识库写入系统
```

V4 的 Agent 不处在最高控制位，只处在模块判断层。V4.1 的 RAG 记忆不直接吃原始日志，只召回复核过的结构化经验卡。

## 2. API 入口边界

### 负责

```text
src.api.main:app
挂载 /api/modules/* 当前模块接口
挂载 /api/accounts 账号、角色、权限、店群范围接口
挂载 /api/health 健康检查
挂载 /api/data/* Mock 数据校验与导入记录
挂载 /api/approvals/* 待确认动作记录
挂载 /api/system/* 系统状态与清理接口
服务 web_demo/index.html 当前模块化前端
```

### 不负责

```text
不挂载旧 demo/debug 入口
不恢复旧商品 / 客户 / 诊断 / evals 入口
不暴露旧运行结果接口
不恢复 backend/server.py
```

## 3. Modules API 边界

### 负责

```text
/api/modules/dashboard                             总览
/api/modules/operating-unit                        经营单元
/api/modules/product                               商品经营列表
/api/modules/competitor                            竞品观察列表
/api/modules/listing                               上新测试台
/api/modules/traffic                               流量测试台
/api/modules/report                                ERP / CRM 报表
/api/modules/todo                                  统一任务池
/api/modules/log                                   日志
/api/modules/task-reports/tasks/{task_id}          任务详情报告
/api/modules/task-reports/candidates/{m}/{id}      候选预警报告
/api/modules/agents                                V4 Agent 注册表
/api/modules/agents/{module}/{entity_id}           V4 模块 Agent 建议
/api/modules/agents/{module}/{entity_id}/tasks     V4 Agent 草案入池
/api/modules/agents/cycle/{target}                 V4 日报 / 周报 Agent
/api/modules/rag-memory                            V4.1 经验记忆摘要
/api/modules/rag-memory/cases                      V4.1 经验卡列表
/api/modules/rag-memory/search                     V4.1 经验召回
/api/modules/rag-memory/feedback/tasks/{task_id}   V4.1 任务回流经验卡草案
/api/modules/rag-memory/cases/{case_id}/approve    V4.1 经验卡复核通过
/api/modules/rag-memory/cases/{case_id}/reject     V4.1 经验卡复核拒绝
```

### 不负责

```text
不直接接真实店铺 API
不直接执行 RPA
不直接发布商品
不直接改价
不直接投放广告
不直接触达客户
不直接退款
不直接回写真实 ERP / CRM
不把未复核原始日志直接写入 RAG
```

## 4. Accounts API 边界

### 负责

```text
/api/accounts                 账号系统总览
/api/accounts/me              当前 Mock 用户
/api/accounts/users           用户列表
/api/accounts/roles           角色列表
/api/accounts/permissions     权限列表
/api/accounts/store-groups    店群范围
/api/accounts/stores          店铺范围
```

### 不负责

```text
不做真实登录
不做真实密码存储
不接企业微信 / 飞书 / 钉钉组织架构
不接真实多租户计费与授权
不把 Mock 账号当作生产账号体系
```

## 5. Task Collaboration 边界

### 负责

```text
候选预警进入统一任务池
Agent 任务草案经人工确认后进入统一任务池
任务完成或复核后可生成经验卡草案
老板 / 总管可以派发任务
运营可以提交处理结果
店群总管可以复核通过或退回
复核通过后任务从待办退出，来源模块释放循环位
日志保留任务流转记录
```

### 状态链路

```text
候选预警 / Agent 草案
→ 已加入任务池
→ 已派发
→ 处理中
→ 已提交 / 待复核
→ 已通过 / 已退回
→ 已归档
→ 经验卡草案
→ 经验卡复核通过 / 拒绝
```

### 不负责

```text
不替运营真实修改商品、库存、价格、投放或客服话术
不跳过人工复核
不把报告建议或 Agent 建议直接变成店铺动作
不把运营主观说法直接变成可召回经验
```

## 6. V4 Agent 边界

### 负责

```text
读取当前模块数据
生成分析摘要
生成证据列表
生成建议动作
生成任务草案
生成人工确认点
生成日报 / 周报草案结构
```

### 不负责

```text
不直接改价
不直接投放
不直接退款
不直接发布商品
不直接回写真实店铺 / ERP / CRM 数据
不绕过账号权限
不绕过任务生命周期
```

## 7. V4.1 RAG Memory 边界

### 负责

```text
存储结构化经验卡
维护经验卡等级 L0-L4
按类目、平台、店铺、问题类型、运营风格、质量分检索
把任务处理结果提炼成经验卡草案
允许老板 / 总管复核经验卡
召回复核通过的 playbook / 历史案例 / 失败案例
```

### 不负责

```text
不直接连接真实向量库
不自动批准经验入库
不把日报 / 周报 / 日志原文直接用于正式召回
不把失败案例当默认建议
不替代 Agent / 任务池 / 人工复核
```

## 8. Workflow 边界

### 负责

```text
读取 Mock ERP / CRM 数据
校验数据关系
识别经营单元
加载经营单元知识档案
生成循环频率策略
生成商品、竞品、上新、流量、动作和报告结果
输出可供模块 API 包装的结构化结果
```

### 不负责

```text
不连接真实商家系统
不绕过平台接口限制
不保存真实客户隐私
不产生真实经营动作
```

## 9. Frontend 边界

### 负责

```text
web_demo/index.html
web_demo/core/router.js
web_demo/core/api-client.js
web_demo/stores/task-store.js
web_demo/modules/*/page.js
展示账号、经营单元、商品、竞品、上新、流量、报表、待办、日志、详情报告、V4 Agent 建议和 V4.1 RAG memory 数据
调用 /api/modules/* 与 /api/accounts
```

### 不负责

```text
不恢复旧单文件前端
不恢复旧标题生成 UI
不恢复旧素材观察 UI
不把当前 Mock 协同页包装成完整企业后台
```

## 10. Scripts / CI 边界

### 负责

```text
scripts/check_version_governance.py   检查版本、日志、旧入口残留
scripts/smoke_test_runtime.py         检查当前 workflow 主链路
scripts/smoke_test_api.py             检查当前产品 API
scripts/start_server.sh               本机启动
scripts/deploy_server.sh              服务器部署
.github/workflows/runtime-smoke-test.yml
                                      CI 执行治理检查和 smoke tests
```

### 不负责

```text
不运行旧 demo 命令
不运行旧 evals 命令
不检查旧 demo route
```

## 11. 当前原则

```text
AI 可以建议，但不能越权执行。
Agent 可以增强模块判断，但不能取代人工确认。
RAG 可以召回复核经验，但不能污染知识库。
账号可以派发任务，但不能绕过经营责任。
运营可以提交结果，但需要总管复核后归档。
报告可以辅助经营判断，但不能替用户承担经营责任。
版本治理必须先于 smoke tests 执行。
文档必须服务当前可运行主线，而不是召回旧模板。
```
