# 模块边界

## 1. 当前边界目标

本文件只描述 v4.4.0 当前 active trunk 的模块边界。

当前产品是：

```text
AI ERP 经营单元协同工作台 + 模块 Agent 增强层 + RAG-ready 运营经验记忆层 + RAG 任务 Agent + 标题主图垂直类目 Agent + 回流任务 Agent
```

当前产品不是：

```text
完整 ERP
完整 CRM
真实企业 SSO
自动运营 Agent
真实店铺后台操作系统
无审核知识库写入系统
自动经营执行系统
自动素材发布系统
自动经验批准系统
```

V4 的 Agent 不处在最高控制位，只处在模块判断层。V4.1 的 RAG 记忆不直接吃原始日志，只召回复核过的结构化经验卡。V4.2 的任务 Agent 只生成任务候选和运营打法。V4.3 的标题主图 Agent 只生成表达策略和测试计划。V4.4 的回流任务 Agent 只生成周期摘要、反馈指标和经验卡草案，不自动批准入库。

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
/api/modules/dashboard                                  总览
/api/modules/operating-unit                             经营单元
/api/modules/product                                    商品经营列表
/api/modules/competitor                                 竞品观察列表
/api/modules/listing                                    上新测试台
/api/modules/traffic                                    流量测试台
/api/modules/report                                     ERP / CRM 报表
/api/modules/todo                                       统一任务池
/api/modules/log                                        日志
/api/modules/task-reports/tasks/{task_id}               任务详情报告
/api/modules/task-reports/candidates/{m}/{id}           候选预警报告
/api/modules/agents                                     V4 Agent 注册表
/api/modules/agents/{module}/{entity_id}                V4 模块 Agent 建议
/api/modules/agents/{module}/{entity_id}/tasks          V4 Agent 草案入池
/api/modules/agents/cycle/{target}                      V4 日报 / 周报 Agent
/api/modules/agents/tasks/generate                      V4.2 自动解析生成任务 Agent
/api/modules/agents/tasks/{task_id}/playbook            V4.2 任务解析运营方式 Agent
/api/modules/agents/creative/{product_id}               V4.3 标题主图垂直类目 Agent
/api/modules/agents/creative/{product_id}/tasks         V4.3 创意测试任务草案入池
/api/modules/feedback-flywheel                          V4.4 回流任务 Agent
/api/modules/feedback-flywheel/cycle/{target}           V4.4 日报 / 周报回流 Agent
/api/modules/feedback-flywheel/cycle/{target}/draft     V4.4 周期经验卡草案
/api/modules/rag-memory                                 V4.1 经验记忆摘要
/api/modules/rag-memory/cases                           V4.1 经验卡列表
/api/modules/rag-memory/search                          V4.1 经验召回
/api/modules/rag-memory/feedback/tasks/{task_id}        V4.1 任务回流经验卡草案
/api/modules/rag-memory/cases/{case_id}/approve         V4.1 经验卡复核通过
/api/modules/rag-memory/cases/{case_id}/reject          V4.1 经验卡复核拒绝
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
不生成真实图片文件
不直接把标题 / 主图发布到店铺后台
不自动批准经验卡入库
```

## 4. Task Collaboration 边界

### 负责

```text
候选预警进入统一任务池
V4.2 Agent 任务候选经人工确认后进入统一任务池
V4.3 创意测试方案经人工确认后进入统一任务池
任务完成或复核后生成经验卡草案
老板 / 总管可以派发任务
运营可以查看任务打法和创意方案并提交处理结果
店群总管可以复核通过或退回
复核通过后任务从待办退出，来源模块释放循环位
日志保留任务流转记录
V4.4 回流 Agent 汇总日报 / 周报和学习候选
```

### 状态链路

```text
候选预警 / Agent 草案 / 创意测试方案
→ 任务候选
→ 人工确认
→ 已加入任务池
→ 已派发
→ 处理中
→ 已提交 / 待复核
→ 已通过 / 已退回
→ 已归档
→ feedbackDraft 经验卡草案
→ 经验卡复核通过 / 拒绝
→ RAG 召回
```

### 不负责

```text
不替运营真实修改商品、库存、价格、投放或客服话术
不跳过人工复核
不把报告建议或 Agent 建议直接变成店铺动作
不把运营主观说法直接变成可召回经验
不把创意方案直接发布成线上主图或标题
```

## 5. Agent 边界

### V4 Module Agent 负责

```text
读取当前模块数据
生成分析摘要
生成证据列表
生成建议动作
生成任务草案
生成人工确认点
生成日报 / 周报草案结构
```

### V4.1 RAG Memory 负责

```text
存储结构化经验卡
维护经验卡等级 L0-L4
按类目、平台、店铺、问题类型、运营风格、质量分检索
把任务处理结果提炼成经验卡草案
允许老板 / 总管复核经验卡
召回复核通过的 playbook / 历史案例 / 失败案例
```

### V4.2 Task Agent 负责

```text
根据模块数据和规则生成任务候选
判断问题类型
召回 RAG 经验卡
计算任务候选置信度
生成证据要求
生成稳健型 / 增长型 / 利润型运营打法
输出人工确认点
```

### V4.3 Creative Agent 负责

```text
读取商品事实、类目 Profile、平台表达规则和竞品信号
召回 RAG 创意经验或问题打法
生成标题方案、主图方向、卖点排序、A/B 测试计划
生成创意测试任务草案
```

### V4.4 Feedback Agent 负责

```text
汇总已完成 / 待处理 / 待复核任务
识别学习候选
生成日报 / 周报回流摘要
生成经验卡草案
展示反馈指标
提示哪些经验需要复核入库
```

### Agent 统一不负责

```text
不直接执行经营动作
不绕过统一任务池
不绕过账号权限
不绕过总管复核
不把 RAG 引用当成唯一事实来源
不自动批准经验入库
不把未复核日志写入正式 RAG
```

## 6. Frontend 边界

```text
web_demo/index.html
web_demo/core/router.js
web_demo/core/api-client.js
web_demo/stores/task-store.js
web_demo/modules/*/page.js
展示账号、经营单元、商品、竞品、上新、流量、报表、待办、日志、详情报告、V4 Agent 建议、V4.1 RAG memory 数据、V4.2 task Agent 数据、V4.3 creative Agent 数据和 V4.4 feedback 数据。
```

## 7. Scripts / CI 边界

```text
scripts/check_version_governance.py
scripts/smoke_test_runtime.py
scripts/smoke_test_api.py
scripts/start_server.sh
scripts/deploy_server.sh
.github/workflows/runtime-smoke-test.yml
```

## 8. 当前原则

```text
AI 可以建议，但不能越权执行。
Agent 可以增强模块判断，但不能取代人工确认。
RAG 可以召回复核经验，但不能污染知识库。
任务 Agent 可以生成候选，但不能绕过统一任务池。
创意 Agent 可以生成表达策略，但不能直接发布商品。
回流 Agent 可以生成经验草案，但不能自动批准入库。
账号可以派发任务，但不能绕过经营责任。
运营可以提交结果，但需要总管复核后归档。
版本治理必须先于 smoke tests 执行。
文档必须服务当前可运行主线，而不是召回旧模板。
```
